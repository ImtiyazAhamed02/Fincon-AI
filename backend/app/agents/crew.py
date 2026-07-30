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
            goal="Analyze only recent company news. Keep output concise and human-friendly.",
            backstory=(
                "Analyze only recent company news. Do not analyze charts or financial statements. "
                "Write like a business news reporter talking to someone new to investing. Do not use jargon."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_technical_agent(self):
        agent = Agent(
            role="Expert Technical Analysis Validator",
            goal="Analyze only historical price and technical indicators. Keep output concise and human-friendly.",
            backstory=(
                "Analyze only historical price and technical indicators. Do not use news. "
                "Write concisely without jargon. Make it easy for beginners to understand."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_risk_agent(self):
        agent = Agent(
            role="Financial Risk Assessment Agent and Validator",
            goal="Analyze volatility, drawdown, beta, VaR, stress scenarios, and market risk.",
            backstory=(
                "Analyze only volatility, drawdown, beta, VaR, stress scenarios, and market risk. "
                "Keep it simple and concise. Do not use complex financial jargon."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_portfolio_agent(self):
        agent = Agent(
            role="Portfolio Manager",
            goal="Analyze the user's holdings, diversification, allocation, and rebalancing.",
            backstory=(
                "Analyze only the user's holdings, diversification, allocation, and rebalancing. "
                "Keep explanations clear, concise, and actionable without jargon."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_fundamental_agent(self):
        agent = Agent(
            role="Fundamental Analyst",
            goal="Analyze company financials, earnings, revenue, profitability, valuation, and competitive position.",
            backstory=(
                "Analyze only company financials, earnings, revenue, profitability, valuation, and competitive position. "
                "Avoid complex jargon and keep the output beginner-friendly."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
        return agent

    def _make_manager_agent(self):
        return Agent(
            role="Chief Investment Editor",
            goal="Combine all agent reports into a single Master Investment Summary.",
            backstory=(
                "You are the Chief Investment Editor. Your job is to read all the agent reports and "
                "combine them into a single, easy-to-read Master Investment Summary that reads like a "
                "financial news article for beginners. Use simple English and short explanations."
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
            description=f"Use the news tool to fetch all news data for {ticker}. Write a concise, beginner-friendly report.",
            expected_output=(
                f"## News Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_stock_news]
        result = crew.kickoff(inputs={"ticker": ticker})
        self._log_agent_output("News Agent", str(result), ticker)
        return {"session_id": self.session_id, "agent": "news", "ticker": ticker, "result": str(result)}

    @rate_limited_gemini
    def analyze_technical(self, ticker: str) -> dict:
        """Run ONLY the Technical Analyst agent."""
        agent = self._make_technical_agent()
        task = Task(
            description=f"Use your tool to fetch technical indicators for {ticker}. Write a concise, beginner-friendly report.",
            expected_output=(
                f"## Technical Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
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
            description=f"Use your tool to fetch risk metrics for {ticker}. Write a concise, beginner-friendly report.",
            expected_output=(
                f"## Risk Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
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
            description=f"Use your tool to fetch fundamental data for {ticker}. Write a concise, beginner-friendly report.",
            expected_output=(
                f"## Fundamental Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
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
            description="Use your tool to retrieve holdings for the active portfolio. Write a concise, beginner-friendly report.",
            expected_output=(
                "## Portfolio Report\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
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
            description=f"Use the news tool to fetch all news data for {ticker}. Write a concise, beginner-friendly report.",
            expected_output=(
                f"## News Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=news_agent,
            async_execution=True,
        )
        tech_task = Task(
            description=f"Use your tool to fetch technical indicators for {ticker}. Write a concise, beginner-friendly report.",
            expected_output=(
                f"## Technical Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=tech_agent,
            async_execution=True,
        )
        risk_task = Task(
            description=f"Use your tool to fetch risk metrics for {ticker}. Write a concise, beginner-friendly report.",
            expected_output=(
                f"## Risk Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=risk_agent,
            context=[news_task, tech_task],
        )
        fund_task = Task(
            description=f"Use your tool to fetch fundamental data for {ticker}. Write a concise, beginner-friendly report.",
            expected_output=(
                f"## Fundamental Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=fund_agent,
            async_execution=True,
        )
        port_task = Task(
            description="Use your tool to retrieve holdings for the active portfolio. Write a concise, beginner-friendly report.",
            expected_output=(
                "## Portfolio Report\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=port_agent,
            async_execution=True,
        )
        manager_task = Task(
            description=(
                f"Review the sentiment, technical, risk, fundamental, and portfolio reports for {company}. "
                f"Generate a balanced, beginner-friendly master investment summary."
            ),
            expected_output=(
                f"# Master Investment Summary for {company} ({ticker})\n\n"
                f"## 📰 News Summary\n"
                f"[Simple explanation derived from News Agent]\n\n"
                f"## 📈 Technical Summary\n"
                f"[Simple explanation derived from Technical Agent]\n\n"
                f"## 🛡️ Risk Summary\n"
                f"[Simple explanation derived from Risk Agent]\n\n"
                f"## 🏢 Fundamental Summary\n"
                f"[Simple explanation derived from Fundamental Agent]\n\n"
                f"## 💼 Portfolio Summary\n"
                f"[Simple explanation derived from Portfolio Agent]\n\n"
                f"---\n\n"
                f"## 🎯 Overall Investment Outlook\n"
                f"[A highly readable, beginner-friendly final verdict combining all factors]"
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
        if "BUY" in res_str or "BULLISH" in res_str:
            rec = "BUY"
        elif "SELL" in res_str or "BEARISH" in res_str:
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
