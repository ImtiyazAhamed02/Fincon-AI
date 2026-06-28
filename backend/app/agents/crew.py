"""
app/agents/crew.py
─────────────────────────────────────────────────────────────────────────────
FinancialCrew — Multi-Agent Financial Analysis Engine
─────────────────────────────────────────────────────────────────────────────

Changes from original:
  - LLM is now sourced from the AI Router (app/services/ai/router.py)
    instead of being hardcoded to Gemini in core/llm.py.
  - `self.llm` is still the single LLM reference used by all agents,
    so the rate_limit decorator can hot-swap it to Grok during a live
    request if Gemini quota is exceeded.
  - All business logic, agent definitions, task structures, and response
    formats are preserved 100%.
"""

from crewai import Agent, Task, Crew, Process
from app.core.llm import primary_llm          # ← now backed by AI Router
from app.agents.tools import get_stock_technical_data, get_stock_news, get_portfolio_data, get_risk_metrics, get_stock_fundamental_data
import uuid
import time
import json
from app.db.client import SQLiteClient
from app.core.logger import logger
from app.core.rate_limit import rate_limited_gemini


class FinancialCrew:
    def __init__(self, session_id: str = None):
        # primary_llm is resolved by the AI Router at startup:
        #   Gemini  → if GEMINI_API_KEY is valid
        #   Grok    → if Gemini is unavailable at startup
        # During a live request the rate_limit decorator may temporarily
        # swap self.llm to the Grok fallback and restore it afterward.
        self.llm = primary_llm
        self.session_id = session_id or str(uuid.uuid4())

    def _log_agent_output(self, agent_name: str, output: str, input_data: str = ""):
        """Utility to save agent reasoning to SQLite."""
        try:
            SQLiteClient.execute_write(
                "INSERT INTO agent_runs (id, session_id, agent_name, input_data, output_data, confidence_score) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), self.session_id, agent_name, str(input_data), str(output), 85.0)
            )
        except Exception as e:
            logger.error(f"Failed to log agent reasoning to SQLite: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Individual Agents
    # ─────────────────────────────────────────────────────────────────────────

    def _make_news_agent(self):
        agent = Agent(
            role="Senior Market News Analyst",
            goal="Analyse news relevance, identify who truly benefits from each story, and write a clear beginner-friendly report.",
            backstory=(
                "You are a financial news sentiment classifier for stock analysis.\n\n"
                "When analyzing a news article for a target stock ticker (e.g., AAPL), follow these strict rules:\n\n"
                "CLASSIFICATION RULES:\n"
                "1. GOOD NEWS — Only classify as positive if the article DIRECTLY benefits the company:\n"
                "   - Earnings beats, product launches, upgrades, partnerships, revenue growth\n"
                "   - Do NOT classify analyst downgrades, executive departures, or stock drops as Good News under any circumstance\n\n"
                "2. CONCERNING NEWS — Classify as concerning if:\n"
                "   - Analyst downgrades (e.g., \"downgraded to Hold/Sell\")\n"
                "   - Key executive departures to competitors\n"
                "   - Stock price drops or sell-offs\n"
                "   - Supply chain issues directly harming the company\n"
                "   - Regulatory or legal threats\n\n"
                "3. NEUTRAL — Use this when:\n"
                "   - The impact on the target company is genuinely unclear\n"
                "   - The article is about the broader industry, not the company directly\n"
                "   - Mixed signals with no dominant direction\n\n"
                "CONFLICT RESOLUTION:\n"
                "- If an article could be both Good and Concerning, pick the DOMINANT signal\n"
                "- Never assign the same article to two categories\n"
                "- When in doubt, prefer Neutral over a forced positive/negative label\n\n"
                "WHO IS AT RISK:\n"
                "- If the article is classified as CONCERNING, \"Who is at risk\" must always include the target company\n"
                "- Never leave \"Who is at risk: Unknown\" on a negative story\n\n"
                "EXCLUSION CRITERIA:\n"
                "- Only exclude articles where the target ticker is mentioned purely incidentally (e.g., in a list of 20 stocks)\n"
                "- Do NOT exclude articles where the company is a primary subject, even if the mention is brief"
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_technical_agent(self):
        agent = Agent(
            role="Expert Technical Analysis Validator",
            goal=(
                "Validate, audit, and interpret all technical indicators from the tool data. "
                "Detect conflicting signals. Classify the trend. Generate Trend Strength Score and Signal Confidence Score. "
                "Use only professional, objective language. Never give direct financial advice."
            ),
            backstory=(
                "You are a senior quantitative technical analyst at an institutional investment firm. "
                "You MUST use only the exact numbers provided by your tools — RSI, MACD, SMA, EMA, Bollinger Bands, Volume, Support/Resistance. "
                "You must explicitly acknowledge and explain any signal conflicts detected by the tool (e.g., overbought RSI + bullish MACD). "
                "Use professional language: say 'Bullish indicators currently outweigh bearish indicators' not 'Buy now'. "
                "Say 'Risk of short-term pullback remains elevated' not 'Sell'. "
                "Always include: Data Source, Analysis Timestamp, Confidence Score, and all Flags from the tool."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_risk_agent(self):
        agent = Agent(
            role="Financial Risk Assessment Agent and Validator",
            goal=(
                "Validate, audit, and interpret all risk metrics from the tool data. "
                "Generate a Risk Score (0–100), Risk Level, and Confidence Score. "
                "Use compliant VaR language. Flag unreliable calculations. "
                "Include the full Methodology section. Never invent or estimate metrics."
            ),
            backstory=(
                "You are a Chief Risk Officer at an institutional asset management firm. "
                "You MUST use only the exact metrics provided by your tool: Volatility, Beta, Alpha, Sharpe, Sortino, VaR, CVaR, Max Drawdown, Correlation. "
                "For VaR, you MUST use this exact compliant interpretation format: "
                "'Based on historical return distributions, 95% of observed returns were better than X%, while 5% were worse. "
                "Actual future losses may exceed this estimate.' "
                "NEVER say 'There is a 5% chance the stock will lose more than X%.' "
                "If the tool provides a Confidence Score below 70, you MUST display a warning: 'LOW CONFIDENCE WARNING: Results may be unreliable.' "
                "Always include the Methodology section with: Data Source, Analysis Period, Benchmark Used, Risk-Free Rate, VaR Confidence Level, VaR Time Horizon, and Trading Days Analyzed. "
                "Flag any issues from the tool's flags field."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_portfolio_agent(self):
        agent = Agent(
            role="Portfolio Manager",
            goal="Evaluate portfolio allocation and diversification quality.",
            backstory=(
                "You construct robust, diversified portfolios optimized for long-term risk-adjusted growth."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_fundamental_agent(self):
        agent = Agent(
            role="Lead Fundamental Analyst",
            goal=(
                "Evaluate corporate growth, margins, financial health, leverage, and valuation multiples. "
                "Classify company financial health and generate a Fundamental Score, Valuation Score, "
                "and Financial Health Score. Outline short-term and long-term investment views."
            ),
            backstory=(
                "You are an institutional fundamental research analyst. You evaluate company financial statements "
                "and multiples (P/E, Forward P/E, PEG, P/S, EV/EBITDA) to determine valuation attractiveness and "
                "operating strength. You rely strictly on the exact figures from your tools. Always include: "
                "Growth Metrics (Revenue, EPS), Operating Margins, Return on Equity (ROE), Return on Assets (ROA), "
                "Debt Ratio, Valuation multiples, and Competitive Analysis."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_manager_agent(self):
        return Agent(
            role="Chief Investment Officer — Final Validation Layer",
            goal=(
                "Aggregate all agent outputs. Check consistency between Risk Assessment and Technical Analysis. "
                "Generate an Overall Market Outlook, Confidence Score, Key Risks, and Key Opportunities. "
                "Ensure all statements are objective, professional, and evidence-based."
            ),
            backstory=(
                "You are the Chief Investment Officer at an institutional investment firm. "
                "You STRICTLY rely on hard data and metrics delivered by your analysts. "
                "Before issuing any recommendation, you MUST validate cross-agent consistency: "
                "e.g., does a High Risk Level align with a Bullish Technical Trend? If not, you must explicitly acknowledge the divergence. "
                "Your final report MUST include exactly these sections: "
                "1. RECOMMENDATION (Buy / Hold / Sell) "
                "2. EVIDENCE (list all supporting metrics and scores with exact values) "
                "3. SUPPORTING INDICATORS (list all indicators that support the recommendation) "
                "4. KEY RISKS (list concrete risks from the risk report) "
                "5. KEY OPPORTUNITIES (list concrete opportunities from the technical report) "
                "6. OVERALL MARKET OUTLOOK (professional, objective assessment) "
                "7. CONFIDENCE SCORE (0–100) with reasoning. "
                "Do NOT invent data. Do NOT give guaranteed profit claims. "
                "Present uncertainty whenever data quality is limited."
            ),
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Single-Agent Task Runners  (separate endpoints)
    # ─────────────────────────────────────────────────────────────────────────

    @rate_limited_gemini
    def analyze_news(self, ticker: str) -> dict:
        """Run ONLY the News Analyst agent."""
        agent = self._make_news_agent()
        task = Task(
            description=(
                f"Use the news tool to fetch all news data for {ticker}. "
                f"Then write a clear, beginner-friendly News Report following these strict rules:\n"
                f"RULE 1: Focus ONLY on {ticker}. Use only articles from the tool's 'good_news', 'potential_concerns', and 'news_worth_watching' fields.\n"
                f"RULE 2: For each article, the tool already tells you the Primary Beneficiary and Primary Risk Holder. "
                f"An article is ONLY classified as 'Good News' if the Primary Beneficiary = Target Company. "
                f"An article is ONLY classified as 'Potential Concerns' if the Primary Risk Holder = Target Company. "
                f"If a competitor is the beneficiary, classify it under 'News Worth Watching' and explain why.\n"
                f"RULE 3: Do NOT use jargon like 'bullish', 'bearish', 'equity', 'P/E ratio'. Write like a business news reporter talking to someone new to investing.\n"
                f"RULE 4: For every news item, write 1-2 simple sentences explaining why it matters specifically for {ticker}.\n"
                f"RULE 5: Copy the 'bottom_line' text exactly from the tool as your final Bottom Line section."
            ),
            expected_output=(
                f"A beginner-friendly News Sentiment Report for **{ticker}** in clean Markdown with exactly these sections:\n\n"
                f"---\n"
                f"## 📰 News Summary\n"
                f"| What We Tracked | Numbers |\n"
                f"| --- | --- |\n"
                f"| ✅ Relevant News Articles | [relevant_articles_count from tool] |\n"
                f"| 🚫 Articles Excluded | [excluded_articles_count from tool] |\n"
                f"| 😊 Good News Stories | [bullish_count from tool] |\n"
                f"| ⚠️ Concerning Stories | [bearish_count from tool] |\n"
                f"| 📄 Neutral Updates | [neutral_count from tool] |\n\n"
                f"---\n"
                f"## 😊 Good News\n"
                f"*Stories where {ticker} is the clear winner — where it directly benefits*\n\n"
                f"For each item in good_news from the tool:\n"
                f"**[Headline] ([Source])**\n"
                f"> 🏢 **Who benefits**: [primary_beneficiary]  |  ⚠️ **Who is at risk**: [primary_risk_holder]\n"
                f"> 💬 *Why it matters for you as an investor: [1-2 plain-English sentences explaining the direct impact on the company's business — revenue, sales, products, or customers]*\n\n"
                f"---\n"
                f"## ⚠️ Potential Concerns\n"
                f"*Stories that raise questions or challenges specifically for {ticker}*\n\n"
                f"For each item in potential_concerns from the tool:\n"
                f"**[Headline] ([Source])**\n"
                f"> 🏢 **Who benefits**: [primary_beneficiary]  |  ⚠️ **Who is at risk**: [primary_risk_holder]\n"
                f"> 💬 *Why it matters: [1-2 plain-English sentences explaining the direct concern for the company's business]*\n\n"
                f"---\n"
                f"## 📄 News Worth Watching\n"
                f"*Stories about the industry, competitors, or related topics — not directly about {ticker} but worth knowing*\n\n"
                f"For each item in news_worth_watching from the tool:\n"
                f"**[Headline] ([Source])**\n"
                f"> 🏢 **Who benefits**: [primary_beneficiary]  |  ⚠️ **Who is at risk**: [primary_risk_holder]\n"
                f"> 💬 *Note: [1-2 plain-English sentences — if a competitor benefits, say so clearly and explain why this is neutral or indirect for {ticker}]*\n\n"
                f"---\n"
                f"## 🛡️ How Confident Are We?\n"
                f"- **Confidence Score**: [confidence_score from tool]% *(we never say 100% — markets are unpredictable)*\n"
                f"- **Why**: [confidence_explanation from tool in plain English — simplify if needed]\n\n"
                f"---\n"
                f"## 📋 Bottom Line\n"
                f"[Copy the exact 'bottom_line' text from the tool here — do not modify it]"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        
        # Bypass Pydantic validation by assigning tools AFTER Crew instantiation
        agent.tools = [get_stock_news]
        
        result = crew.kickoff(inputs={"ticker": ticker})
        self._log_agent_output("News Agent", str(result), ticker)
        return {"session_id": self.session_id, "agent": "news", "ticker": ticker, "result": str(result)}

    @rate_limited_gemini
    def analyze_technical(self, ticker: str) -> dict:
        """Run ONLY the Technical Analyst agent."""
        agent = self._make_technical_agent()
        task = Task(
            description=(
                f"Use your tool to fetch all technical indicators for {ticker}. "
                f"Validate, audit, and interpret each indicator. Detect any signal conflicts. "
                f"Classify the trend and generate a Trend Strength Score and Signal Confidence Score."
            ),
            expected_output=(
                f"An institutional-grade Technical Analysis Report for {ticker} formatted as clean Markdown (no raw JSON). "
                f"Format the sections using headings (##), bullet lists, and tables where appropriate. It MUST include:\n"
                f"1. PRICE & INDICATOR SUMMARY: Current Price, RSI(14) with interpretation, MACD Line/Signal/Histogram with interpretation, SMA20, SMA50, EMA12, EMA26, Bollinger Bands (Upper/Middle/Lower), ATR(14)\n"
                f"2. VOLUME ANALYSIS: Current Volume, 20D Average Volume, Volume Ratio, Volume Trend\n"
                f"3. SUPPORT & RESISTANCE: Pivot Point, R1, R2, S1, S2, 52W High, 52W Low\n"
                f"4. MOMENTUM ANALYSIS: Price vs SMA20, Price vs SMA50, Bollinger Band position\n"
                f"5. SIGNAL CONFLICTS: List all detected conflicts with professional explanations\n"
                f"6. TREND CLASSIFICATION: Strong Bullish / Bullish / Neutral / Bearish / Strong Bearish + Trend Score (0-100)\n"
                f"7. SIGNAL CONFIDENCE SCORE (0-100) with warning if below 70\n"
                f"8. DATA FLAGS: List all quality flags\n"
                f"9. METHODOLOGY: Data Source, Analysis Timestamp"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_stock_technical_data]
        result = crew.kickoff(inputs={"ticker": ticker})
        self._log_agent_output("Technical Agent", str(result), ticker)
        return {"session_id": self.session_id, "agent": "technical", "ticker": ticker, "result": str(result)}

    @rate_limited_gemini
    def analyze_risk(self, ticker: str) -> dict:
        """Run ONLY the Risk Officer agent."""
        agent = self._make_risk_agent()
        task = Task(
            description=(
                f"Use your tool to fetch all risk metrics for {ticker}. "
                f"Validate the calculations. Generate a Risk Score and Risk Level. "
                f"Use compliant VaR language. Flag any unreliable data. "
                f"Include the complete Methodology section."
            ),
            expected_output=(
                f"An institutional-grade Risk Assessment Report for {ticker} formatted as clean Markdown (no raw JSON). "
                f"Format the sections using headings (##), bullet lists, and tables where appropriate. It MUST include:\n"
                f"1. RISK METRICS TABLE: Annualized Volatility, Beta, Alpha (Annualized), Max Drawdown, Sharpe Ratio, Sortino Ratio, Downside Deviation, Benchmark Correlation\n"
                f"2. VALUE AT RISK: VaR (95%, 1-Day) with COMPLIANT interpretation: 'Based on historical return distributions, 95% of observed returns were better than X%, while 5% were worse. Actual future losses may exceed this estimate.'\n"
                f"3. CVAR / EXPECTED SHORTFALL: CVaR (95%) value\n"
                f"4. RISK SCORE: Numeric score 0–100\n"
                f"5. RISK LEVEL: Low / Moderate / High / Very High\n"
                f"6. CONFIDENCE SCORE: 0–100 — display 'LOW CONFIDENCE WARNING' if below 70\n"
                f"7. DATA FLAGS: List all flags (INSUFFICIENT_DATA, MISSING_BENCHMARK, EXTREME_BETA_OUTLIER, etc.)\n"
                f"8. METHODOLOGY: Data Source, Analysis Period, Benchmark Used, Risk-Free Rate, VaR Confidence Level, VaR Time Horizon, Trading Days Analyzed"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_risk_metrics]
        result = crew.kickoff(inputs={"ticker": ticker})
        self._log_agent_output("Risk Agent", str(result), ticker)
        return {"session_id": self.session_id, "agent": "risk", "ticker": ticker, "result": str(result)}

    @rate_limited_gemini
    def analyze_fundamental(self, ticker: str) -> dict:
        """Run ONLY the Fundamental Analyst agent."""
        agent = self._make_fundamental_agent()
        task = Task(
            description=f"Use your tool to fetch all fundamental and financial data for {ticker}. Assess valuation and health.",
            expected_output=(
                f"An institutional-grade Fundamental Analysis Report for {ticker} formatted as clean Markdown (no raw JSON). "
                f"Format the sections using headings (##), bullet lists, and tables where appropriate. It MUST include:\n"
                f"1. FINANCIAL METRICS: Revenue Growth, EPS Growth, Operating Margin, Free Cash Flow, Debt Ratio, ROE, ROA\n"
                f"2. VALUATION SUMMARY: P/E, Forward P/E, PEG, Price/Sales, EV/EBITDA\n"
                f"3. COMPETITIVE ANALYSIS: Market Position, Moat, Competitor Comparison\n"
                f"4. SCORES: Fundamental Score, Valuation Score, Financial Health Score (all 0-100)\n"
                f"5. VIEWS: Short-Term View, Long-Term View"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_stock_fundamental_data]
        result = crew.kickoff(inputs={"ticker": ticker})
        self._log_agent_output("Fundamental Agent", str(result), ticker)
        return {"session_id": self.session_id, "agent": "fundamental", "ticker": ticker, "result": str(result)}

    @rate_limited_gemini
    def analyze_portfolio(self, portfolio_id: str = None) -> dict:
        """Run ONLY the Portfolio Manager agent."""
        agent = self._make_portfolio_agent()
        p_id = portfolio_id or "default_portfolio"
        task = Task(
            description=(
                "Use your tool to retrieve holdings for the active portfolio and evaluate them. "
                "Assess diversification quality, sector exposure, and allocation balance. "
                "Provide concrete rebalancing suggestions and highlight concentration risks."
            ),
            expected_output=(
                "A detailed portfolio review report formatted as clean Markdown (no raw JSON). "
                "Format the sections using headings (##), bullet lists, and tables where appropriate. It MUST contain:\n"
                "1. PORTFOLIO VALUE: total value of the active portfolio\n"
                "2. DIVERSIFICATION SCORE: 0-10 score with explanation\n"
                "3. SECTOR EXPOSURE: percentage of allocation by sector\n"
                "4. CONCENTRATION RISK: assessment of high-weight positions\n"
                "5. CORRELATION ANALYSIS: correlation between holdings\n"
                "6. REBALANCING SUGGESTIONS: concrete changes to improve diversification\n"
                "7. PORTFOLIO RISK SCORE: 0-100 score"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        
        # Bypass Pydantic validation by assigning tools AFTER Crew instantiation
        agent.tools = [get_portfolio_data]
        
        result = crew.kickoff(inputs={"portfolio_id": p_id})
        self._log_agent_output("Portfolio Agent", str(result), p_id)
        return {"session_id": self.session_id, "agent": "portfolio", "portfolio_id": p_id, "result": str(result)}

    # ─────────────────────────────────────────────────────────────────────────
    # Full Multi-Agent Crew Run
    # ─────────────────────────────────────────────────────────────────────────

    @rate_limited_gemini
    def analyze_stock(self, company: str, ticker: str) -> dict:
        """Run the full multi-agent crew: News → Technical → Risk → Fundamental → Portfolio → Manager."""
        news_agent    = self._make_news_agent()
        tech_agent    = self._make_technical_agent()
        risk_agent    = self._make_risk_agent()
        fund_agent    = self._make_fundamental_agent()
        port_agent    = self._make_portfolio_agent()
        manager_agent = self._make_manager_agent()

        news_task = Task(
            description=(
                f"Use the news tool to fetch all news data for {ticker}. "
                f"Then write a clear, beginner-friendly News Report following these strict rules:\n"
                f"RULE 1: Focus ONLY on {ticker}. Use only articles from the tool's 'good_news', 'potential_concerns', and 'news_worth_watching' fields.\n"
                f"RULE 2: For each article, the tool already tells you the Primary Beneficiary and Primary Risk Holder. "
                f"An article is ONLY classified as 'Good News' if the Primary Beneficiary = Target Company. "
                f"An article is ONLY classified as 'Potential Concerns' if the Primary Risk Holder = Target Company. "
                f"If a competitor is the beneficiary, classify it under 'News Worth Watching' and explain why.\n"
                f"RULE 3: Do NOT use jargon like 'bullish', 'bearish', 'equity', 'P/E ratio'. Write like a business news reporter talking to someone new to investing.\n"
                f"RULE 4: For every news item, write 1-2 simple sentences explaining why it matters specifically for {ticker}.\n"
                f"RULE 5: Copy the 'bottom_line' text exactly from the tool as your final Bottom Line section."
            ),
            expected_output=(
                f"A beginner-friendly News Sentiment Report for **{company} ({ticker})** in clean Markdown with exactly these sections:\n\n"
                f"---\n"
                f"## 📰 News Summary\n"
                f"| What We Tracked | Numbers |\n"
                f"| --- | --- |\n"
                f"| ✅ Relevant News Articles | [relevant_articles_count from tool] |\n"
                f"| 🚫 Articles Excluded | [excluded_articles_count from tool] |\n"
                f"| 😊 Good News Stories | [bullish_count from tool] |\n"
                f"| ⚠️ Concerning Stories | [bearish_count from tool] |\n"
                f"| 📄 Neutral Updates | [neutral_count from tool] |\n\n"
                f"---\n"
                f"## 😊 Good News\n"
                f"*Stories where {company} is the clear winner — where it directly benefits*\n\n"
                f"For each item in good_news from the tool:\n"
                f"**[Headline] ([Source])**\n"
                f"> 🏢 **Who benefits**: [primary_beneficiary]  |  ⚠️ **Who is at risk**: [primary_risk_holder]\n"
                f"> 💬 *Why it matters for you as an investor: [1-2 plain-English sentences explaining the direct impact on the company's business — revenue, sales, products, or customers]*\n\n"
                f"---\n"
                f"## ⚠️ Potential Concerns\n"
                f"*Stories that raise questions or challenges specifically for {company}*\n\n"
                f"For each item in potential_concerns from the tool:\n"
                f"**[Headline] ([Source])**\n"
                f"> 🏢 **Who benefits**: [primary_beneficiary]  |  ⚠️ **Who is at risk**: [primary_risk_holder]\n"
                f"> 💬 *Why it matters: [1-2 plain-English sentences explaining the direct concern for the company's business]*\n\n"
                f"---\n"
                f"## 📄 News Worth Watching\n"
                f"*Stories about the industry, competitors, or related topics — not directly about {company} but worth knowing*\n\n"
                f"For each item in news_worth_watching from the tool:\n"
                f"**[Headline] ([Source])**\n"
                f"> 🏢 **Who benefits**: [primary_beneficiary]  |  ⚠️ **Who is at risk**: [primary_risk_holder]\n"
                f"> 💬 *Note: [1-2 plain-English sentences — if a competitor benefits, say so clearly and explain why this is neutral or indirect for {company}]*\n\n"
                f"---\n"
                f"## 🛡️ How Confident Are We?\n"
                f"- **Confidence Score**: [confidence_score from tool]% *(we never say 100% — markets are unpredictable)*\n"
                f"- **Why**: [confidence_explanation from tool in plain English — simplify if needed]\n\n"
                f"---\n"
                f"## 📋 Bottom Line\n"
                f"[Copy the exact 'bottom_line' text from the tool here — do not modify it]"
            ),
            agent=news_agent,
            async_execution=True,
        )
        tech_task = Task(
            description=(
                f"Use your tool to fetch all technical indicators for {ticker}. "
                f"Validate, audit, and interpret each indicator. Detect any signal conflicts. "
                f"Classify the trend and generate a Trend Strength Score and Signal Confidence Score."
            ),
            expected_output=(
                f"An institutional-grade Technical Analysis Report for {company} ({ticker}) formatted as clean Markdown (no raw JSON). "
                f"Format the sections using headings (##), bullet lists, and tables where appropriate. It MUST include:\n"
                f"1. PRICE & INDICATOR SUMMARY: Current Price, RSI(14) with interpretation, MACD Line/Signal/Histogram with interpretation, SMA20, SMA50, EMA12, EMA26, Bollinger Bands, ATR(14)\n"
                f"2. VOLUME ANALYSIS: Current Volume, 20D Average Volume, Volume Ratio, Volume Trend\n"
                f"3. SUPPORT & RESISTANCE: Pivot Point, R1, R2, S1, S2, 52W High, 52W Low\n"
                f"4. MOMENTUM ANALYSIS: Price vs SMA20/SMA50, Bollinger Band position\n"
                f"5. SIGNAL CONFLICTS: All detected conflicts with professional explanations\n"
                f"6. TREND CLASSIFICATION: Label + Trend Score (0-100)\n"
                f"7. SIGNAL CONFIDENCE SCORE (0-100) with warning if below 70\n"
                f"8. DATA FLAGS and METHODOLOGY"
            ),
            agent=tech_agent,
            async_execution=True,
        )
        risk_task = Task(
            description=(
                f"Use your tool to fetch all risk metrics for {ticker}. "
                f"Validate the calculations. Enforce compliant VaR language. "
                f"Include the complete Methodology section."
            ),
            expected_output=(
                f"An institutional-grade Risk Assessment Report for {company} ({ticker}) formatted as clean Markdown (no raw JSON). "
                f"Format the sections using headings (##), bullet lists, and tables where appropriate. It MUST include:\n"
                f"1. RISK METRICS TABLE: Volatility, Beta, Alpha, Max Drawdown, Sharpe, Sortino, Downside Deviation, Correlation\n"
                f"2. VALUE AT RISK (compliant): 'Based on historical return distributions, 95% of observed returns were better than X%, while 5% were worse. Actual future losses may exceed this estimate.'\n"
                f"3. CVAR / EXPECTED SHORTFALL\n"
                f"4. RISK SCORE (0-100), RISK LEVEL (Low/Moderate/High/Very High)\n"
                f"5. CONFIDENCE SCORE with LOW CONFIDENCE WARNING if below 70\n"
                f"6. DATA FLAGS and METHODOLOGY section"
            ),
            agent=risk_agent,
            context=[news_task, tech_task],
        )
        fund_task = Task(
            description=f"Use your tool to fetch all fundamental and financial data for {ticker}. Assess valuation metrics and operational growth.",
            expected_output=(
                f"An institutional-grade Fundamental Analysis Report for {company} ({ticker}) formatted as clean Markdown (no raw JSON). "
                f"Format the sections using headings (##), bullet lists, and tables where appropriate. It MUST include:\n"
                f"1. FINANCIAL METRICS: Revenue Growth, EPS Growth, Operating Margin, Free Cash Flow, Debt Ratio, ROE, ROA\n"
                f"2. VALUATION SUMMARY: P/E, Forward P/E, PEG, Price/Sales, EV/EBITDA\n"
                f"3. COMPETITIVE ANALYSIS: Market Position, Moat, Competitor Comparison\n"
                f"4. SCORES: Fundamental Score, Valuation Score, Financial Health Score\n"
                f"5. VIEWS: Short-Term View, Long-Term View"
            ),
            agent=fund_agent,
            async_execution=True,
        )
        port_task = Task(
            description=(
                "Use your tool to retrieve holdings for the active portfolio and evaluate them. "
                "Assess diversification quality, sector exposure, and allocation balance. "
                "Highlight concentration risks and suggest rebalancing."
            ),
            expected_output=(
                "A detailed portfolio review report formatted as clean Markdown (no raw JSON). "
                "Format the sections using headings (##), bullet lists, and tables where appropriate. It MUST contain:\n"
                "1. PORTFOLIO VALUE: total value of the active portfolio\n"
                "2. DIVERSIFICATION SCORE: 0-10 score with explanation\n"
                "3. SECTOR EXPOSURE: percentage of allocation by sector\n"
                "4. CONCENTRATION RISK: assessment of high-weight positions\n"
                "5. CORRELATION ANALYSIS: correlation between holdings\n"
                "6. REBALANCING SUGGESTIONS: concrete changes to improve diversification\n"
                "7. PORTFOLIO RISK SCORE: 0-100 score\n"
                "If no portfolio exists, output 'No portfolio available for analysis.' without throwing errors."
            ),
            agent=port_agent,
            async_execution=True,
        )
        manager_task = Task(
            description=(
                f"Review the sentiment, technical, risk, fundamental, and portfolio reports for {company}. "
                f"Generate a balanced, institutional-grade master investment summary. "
                f"Never provide direct buy/sell advice; use institutional-style research reporting."
            ),
            expected_output=(
                f"An institutional-grade Master Investment Report for {company} ({ticker}) with exactly these sections:\n"
                f"1. MASTER INVESTMENT SUMMARY: A high-level consolidated report overview\n"
                f"2. SENTIMENT SUMMARY: Detailed summary of news drivers, sources, and reliability tiers\n"
                f"3. TECHNICAL SUMMARY: Detailed summary of multi-timeframe trends, conflicts, risk traps, and setups\n"
                f"4. RISK SUMMARY: Detailed summary of risk attribution, stress tests, and scenario simulations\n"
                f"5. FUNDAMENTAL SUMMARY: Detailed summary of margins, health scores, valuation, and competitor comparisons\n"
                f"6. PORTFOLIO SUMMARY: Detailed summary of current portfolio health and rebalancing recommendations\n"
                f"7. OVERALL CONVICTION SCORE (0-100) with reasoning\n"
                f"8. OVERALL CONFIDENCE SCORE (0-100) with explanation\n"
                f"9. BULL CASE: Supporting factors for an upward trajectory\n"
                f"10. BEAR CASE: Impeding factors or downside catalysts\n"
                f"11. NEUTRAL CASE: Consolidating factors"
            ),
            agent=manager_agent,
            context=[news_task, tech_task, risk_task, fund_task, port_task],
        )

        crew = Crew(
            agents=[news_agent, tech_agent, risk_agent, fund_agent, port_agent, manager_agent],
            tasks=[news_task, tech_task, risk_task, fund_task, port_task, manager_task],
            process=Process.sequential,
        )

        # Bypass Pydantic validation by assigning tools AFTER Crew instantiation
        news_agent.tools = [get_stock_news]
        tech_agent.tools = [get_stock_technical_data]
        risk_agent.tools = [get_risk_metrics]
        fund_agent.tools = [get_stock_fundamental_data]
        port_agent.tools = [get_portfolio_data]

        start_time = time.time()
        result = crew.kickoff(inputs={"company": company, "ticker": ticker})
        end_time = time.time()
        duration_sec = int(end_time - start_time)

        self._log_agent_output("News Agent",        "Executed News Task",        ticker)
        self._log_agent_output("Technical Agent",   "Executed Technical Task",   ticker)
        self._log_agent_output("Risk Agent",        "Executed Risk Task",        ticker)
        self._log_agent_output("Fundamental Agent", "Executed Fundamental Task", ticker)
        self._log_agent_output("Portfolio Agent",   "Executed Portfolio Task",   ticker)
        self._log_agent_output("Manager Agent",     str(result),                 ticker)

        # Parse recommendation roughly
        res_str = str(result).upper()
        if "CONVICTION: HIGH" in res_str or "BULLISH" in res_str:
            rec = "BUY"
        elif "BEARISH" in res_str:
            rec = "SELL"
        else:
            rec = "HOLD"

        # Save to SQLite history
        try:
            SQLiteClient.execute_write(
                "INSERT INTO analysis_history (id, session_id, user_id, ticker, company_name, recommendation, score, agents, summary, duration) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    self.session_id,
                    "default_user",
                    ticker,
                    company,
                    rec,
                    85,
                    json.dumps(["News", "Technical", "Risk", "Fundamental", "Portfolio", "CIO"]),
                    str(result),
                    f"{duration_sec}s"
                )
            )
        except Exception as e:
            logger.error(f"Failed to log session summary to SQLite: {e}")

        return {
            "session_id": self.session_id,
            "company": company,
            "ticker": ticker,
            "recommendation": str(result),
        }


def get_financial_crew(session_id: str = None) -> FinancialCrew:
    return FinancialCrew(session_id=session_id)
