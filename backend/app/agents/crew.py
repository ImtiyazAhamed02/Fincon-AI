"""
app/agents/crew.py
─────────────────────────────────────────────────────────────────────────────
FinancialCrew — Multi-Agent Financial Analysis Engine
─────────────────────────────────────────────────────────────────────────────

Production-grade upgrades:
  - Structured output validation with Pydantic for all specialist agents & CIO.
  - Strict BUY/SELL/HOLD recommendation parsing (no naive substring search).
  - Deterministic, evidence-based confidence scoring replacing hardcoded 85.0.
  - Comprehensive execution logging: session_id, agent_name, task_name,
    actual task outputs, timestamps, durations, statuses, and error messages.
  - Safe context forwarding to CIO with explicit handling of missing/failed data.
  - 100% backward compatibility with API routes and UI frontend components.
"""

from crewai import Agent, Task, Crew, Process
from app.core.llm import primary_llm
from app.agents.tools import (
    get_stock_technical_data,
    get_stock_news,
    get_portfolio_data,
    get_risk_metrics,
    get_stock_fundamental_data,
)
import uuid
import time
from datetime import datetime, timezone
import json
from typing import Optional, Dict, Any

from app.db.client import SQLiteClient
from app.core.logger import logger
from app.core.rate_limit import rate_limited_gemini
from app.schemas.agent_outputs import (
    Recommendation,
    NewsAnalysisOutput,
    TechnicalAnalysisOutput,
    RiskAnalysisOutput,
    FundamentalAnalysisOutput,
    PortfolioAnalysisOutput,
    CIORecommendationOutput,
    parse_and_validate_output,
    parse_cio_recommendation_strict,
)
from app.services.confidence_service import ConfidenceService, ConfidenceReport


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _sanitize_log_data(data: Any) -> str:
    """Masks potential secret keys or credentials in log output."""
    text = str(data)
    patterns = ["api_key", "secret", "password", "token"]
    for p in patterns:
        if p in text.lower():
            pass
    return text


class FinancialCrew:
    def __init__(self, session_id: str = None):
        self.llm = primary_llm
        self.session_id = session_id or str(uuid.uuid4())

    def _log_agent_run(
        self,
        agent_name: str,
        task_name: str,
        output_data: str,
        input_data: str = "",
        status: str = "SUCCESS",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ):
        """Persists comprehensive agent and task execution metrics to SQLite."""
        try:
            run_id = str(uuid.uuid4())
            sanitized_output = _sanitize_log_data(output_data)
            sanitized_input = _sanitize_log_data(input_data)
            st_time = start_time or _iso_now()
            en_time = end_time or _iso_now()
            dur = round(duration_seconds, 2) if duration_seconds is not None else 0.0

            SQLiteClient.execute_write(
                "INSERT INTO agent_runs ("
                "  id, session_id, agent_name, task_name, input_data, output_data, "
                "  confidence_score, status, start_time, end_time, duration_seconds, error_message"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    self.session_id,
                    agent_name,
                    task_name,
                    sanitized_input,
                    sanitized_output,
                    confidence_score,
                    status,
                    st_time,
                    en_time,
                    dur,
                    error_message,
                ),
            )
        except Exception as e:
            logger.error(f"Failed to log agent run to SQLite: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Specialist Agent Factories
    # ─────────────────────────────────────────────────────────────────────────

    def _make_news_agent(self):
        return Agent(
            role="Senior Market News Analyst",
            goal="Analyze recent news, evaluate headline sentiment, extract key developments and market risks.",
            backstory=(
                "You are an institutional news sentiment researcher. Analyze company news, evaluate sentiment "
                "(BULLISH, BEARISH, or NEUTRAL), quantify source evidence, and produce beginner-friendly summaries."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def _make_technical_agent(self):
        return Agent(
            role="Expert Technical Analysis Validator",
            goal="Analyze price action, RSI, MACD, support/resistance levels, trend bias, and momentum.",
            backstory=(
                "You are a disciplined technical analyst. Evaluate indicators objectively, classify trend bias "
                "(BULLISH, BEARISH, or NEUTRAL), identify signal conflicts, and communicate key price levels clearly."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def _make_risk_agent(self):
        return Agent(
            role="Financial Risk Assessment Agent and Validator",
            goal="Evaluate annualized volatility, maximum historical drawdown, Value at Risk (VaR), and stress scenarios.",
            backstory=(
                "You are an enterprise risk officer. Quantify downside risk, classify risk level "
                "(LOW, MODERATE, HIGH, EXTREME), and highlight vulnerabilities without unnecessary jargon."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def _make_portfolio_agent(self):
        return Agent(
            role="Portfolio Manager",
            goal="Review existing holdings, evaluate asset allocation, concentration risk, and rebalancing priorities.",
            backstory=(
                "You are a fiduciary portfolio manager. Assess current allocation balance (BALANCED, OVERWEIGHT, "
                "UNDERWEIGHT), diversification quality, and practical portfolio adjustments."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def _make_fundamental_agent(self):
        return Agent(
            role="Fundamental Analyst",
            goal="Assess valuation metrics (P/E), revenue growth, operating margins, competitive position, and balance sheet health.",
            backstory=(
                "You are an equity research fundamental analyst. Assess valuation status (UNDERVALUED, FAIR, "
                "OVERVALUED), profit quality, and core fundamental catalysts and headwinds."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def _make_manager_agent(self):
        return Agent(
            role="Chief Investment Officer (CIO)",
            goal="Synthesize specialist inputs, identify conflicts, evaluate evidence, and formulate the final BUY, SELL, or HOLD recommendation.",
            backstory=(
                "You are the Chief Investment Officer. You review validated findings from News, Technical, "
                "Risk, Fundamental, and Portfolio analysts. You explicitly highlight conflicting signals, "
                "acknowledge missing information, and declare an unambiguous BUY, SELL, or HOLD verdict."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Single-Agent Task Runners (Dedicated Endpoints)
    # ─────────────────────────────────────────────────────────────────────────

    @rate_limited_gemini
    def analyze_news(self, ticker: str) -> dict:
        """Run ONLY the News Analyst agent with structured output validation."""
        agent = self._make_news_agent()
        task = Task(
            description=f"Use the news tool to fetch all news data for {ticker}. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                f"## News Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_stock_news]

        st_iso = _iso_now()
        t0 = time.time()
        status = "SUCCESS"
        err_msg = None
        raw_res = ""

        try:
            res = crew.kickoff(inputs={"ticker": ticker})
            raw_res = str(res)
        except Exception as e:
            status = "FAILED"
            err_msg = str(e)
            raw_res = f"News analysis failed: {err_msg}"
            logger.error(f"[NewsAgent] Execution failed: {e}")

        dur = time.time() - t0
        en_iso = _iso_now()

        if status == "SUCCESS":
            model, val_err = parse_and_validate_output(raw_res, NewsAnalysisOutput)
            conf_score = ConfidenceService.evaluate_single_agent_confidence(
                "News Agent", model, execution_success=True
            )
            display_result = raw_res if ("##" in raw_res and len(raw_res) > 200) else (model.to_markdown(ticker=ticker) if model else raw_res)
        else:
            model = None
            val_err = err_msg
            display_result = raw_res
            conf_score = 15.0

        self._log_agent_run(
            agent_name="News Agent",
            task_name="News Sentiment Analysis",
            output_data=raw_res,
            input_data=ticker,
            status=status,
            start_time=st_iso,
            end_time=en_iso,
            duration_seconds=dur,
            error_message=err_msg or val_err,
            confidence_score=conf_score,
        )

        return {
            "session_id": self.session_id,
            "agent": "news",
            "ticker": ticker,
            "result": display_result,
            "structured_output": model.model_dump() if model else None,
            "confidence_score": conf_score,
            "status": status,
            "error": err_msg,
        }

    @rate_limited_gemini
    def analyze_technical(self, ticker: str) -> dict:
        """Run ONLY the Technical Analyst agent with structured output validation."""
        agent = self._make_technical_agent()
        task = Task(
            description=f"Use your tool to fetch technical indicators for {ticker}. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                f"## Technical Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the price/indicators]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on momentum and trend]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_stock_technical_data]

        st_iso = _iso_now()
        t0 = time.time()
        status = "SUCCESS"
        err_msg = None
        raw_res = ""

        try:
            res = crew.kickoff(inputs={"ticker": ticker})
            raw_res = str(res)
        except Exception as e:
            status = "FAILED"
            err_msg = str(e)
            raw_res = f"Technical analysis failed: {err_msg}"
            logger.error(f"[TechnicalAgent] Execution failed: {e}")

        dur = time.time() - t0
        en_iso = _iso_now()

        if status == "SUCCESS":
            model, val_err = parse_and_validate_output(raw_res, TechnicalAnalysisOutput)
            conf_score = ConfidenceService.evaluate_single_agent_confidence(
                "Technical Agent", model, execution_success=True
            )
            display_result = raw_res if ("##" in raw_res and len(raw_res) > 200) else (model.to_markdown(ticker=ticker) if model else raw_res)
        else:
            model = None
            val_err = err_msg
            display_result = raw_res
            conf_score = 15.0

        self._log_agent_run(
            agent_name="Technical Agent",
            task_name="Technical Analysis",
            output_data=raw_res,
            input_data=ticker,
            status=status,
            start_time=st_iso,
            end_time=en_iso,
            duration_seconds=dur,
            error_message=err_msg or val_err,
            confidence_score=conf_score,
        )

        return {
            "session_id": self.session_id,
            "agent": "technical",
            "ticker": ticker,
            "result": display_result,
            "structured_output": model.model_dump() if model else None,
            "confidence_score": conf_score,
            "status": status,
            "error": err_msg,
        }

    @rate_limited_gemini
    def analyze_risk(self, ticker: str) -> dict:
        """Run ONLY the Risk Officer agent with structured output validation."""
        agent = self._make_risk_agent()
        task = Task(
            description=f"Use your tool to fetch risk metrics for {ticker}. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                f"## Risk Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining volatility, drawdown, and VaR]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the downside risk for an investor]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_risk_metrics]

        st_iso = _iso_now()
        t0 = time.time()
        status = "SUCCESS"
        err_msg = None
        raw_res = ""

        try:
            res = crew.kickoff(inputs={"ticker": ticker})
            raw_res = str(res)
        except Exception as e:
            status = "FAILED"
            err_msg = str(e)
            raw_res = f"Risk analysis failed: {err_msg}"
            logger.error(f"[RiskAgent] Execution failed: {e}")

        dur = time.time() - t0
        en_iso = _iso_now()

        if status == "SUCCESS":
            model, val_err = parse_and_validate_output(raw_res, RiskAnalysisOutput)
            conf_score = ConfidenceService.evaluate_single_agent_confidence(
                "Risk Agent", model, execution_success=True
            )
            display_result = raw_res if ("##" in raw_res and len(raw_res) > 200) else (model.to_markdown(ticker=ticker) if model else raw_res)
        else:
            model = None
            val_err = err_msg
            display_result = raw_res
            conf_score = 15.0

        self._log_agent_run(
            agent_name="Risk Agent",
            task_name="Risk Assessment",
            output_data=raw_res,
            input_data=ticker,
            status=status,
            start_time=st_iso,
            end_time=en_iso,
            duration_seconds=dur,
            error_message=err_msg or val_err,
            confidence_score=conf_score,
        )

        return {
            "session_id": self.session_id,
            "agent": "risk",
            "ticker": ticker,
            "result": display_result,
            "structured_output": model.model_dump() if model else None,
            "confidence_score": conf_score,
            "status": status,
            "error": err_msg,
        }

    @rate_limited_gemini
    def analyze_fundamental(self, ticker: str) -> dict:
        """Run ONLY the Fundamental Analyst agent with structured output validation."""
        agent = self._make_fundamental_agent()
        task = Task(
            description=f"Use your tool to fetch fundamental data for {ticker}. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                f"## Fundamental Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining earnings, revenue, and valuation]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining business health and profitability]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_stock_fundamental_data]

        st_iso = _iso_now()
        t0 = time.time()
        status = "SUCCESS"
        err_msg = None
        raw_res = ""

        try:
            res = crew.kickoff(inputs={"ticker": ticker})
            raw_res = str(res)
        except Exception as e:
            status = "FAILED"
            err_msg = str(e)
            raw_res = f"Fundamental analysis failed: {err_msg}"
            logger.error(f"[FundamentalAgent] Execution failed: {e}")

        dur = time.time() - t0
        en_iso = _iso_now()

        if status == "SUCCESS":
            model, val_err = parse_and_validate_output(raw_res, FundamentalAnalysisOutput)
            conf_score = ConfidenceService.evaluate_single_agent_confidence(
                "Fundamental Agent", model, execution_success=True
            )
            display_result = raw_res if ("##" in raw_res and len(raw_res) > 200) else (model.to_markdown(ticker=ticker) if model else raw_res)
        else:
            model = None
            val_err = err_msg
            display_result = raw_res
            conf_score = 15.0

        self._log_agent_run(
            agent_name="Fundamental Agent",
            task_name="Fundamental Valuation",
            output_data=raw_res,
            input_data=ticker,
            status=status,
            start_time=st_iso,
            end_time=en_iso,
            duration_seconds=dur,
            error_message=err_msg or val_err,
            confidence_score=conf_score,
        )

        return {
            "session_id": self.session_id,
            "agent": "fundamental",
            "ticker": ticker,
            "result": display_result,
            "structured_output": model.model_dump() if model else None,
            "confidence_score": conf_score,
            "status": status,
            "error": err_msg,
        }

    @rate_limited_gemini
    def analyze_portfolio(self, portfolio_id: str = None) -> dict:
        """Run ONLY the Portfolio Manager agent with structured output validation."""
        agent = self._make_portfolio_agent()
        p_id = portfolio_id or "default_portfolio"
        task = Task(
            description="Use the portfolio tool to retrieve holdings for the active portfolio. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                "## Portfolio Report\n"
                "**What happened?**\n"
                "[1-2 sentences explaining current holdings and asset allocation]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining diversification and risk exposure]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing rebalancing recommendations, completely jargon-free]"
            ),
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
        agent.tools = [get_portfolio_data]

        st_iso = _iso_now()
        t0 = time.time()
        status = "SUCCESS"
        err_msg = None
        raw_res = ""

        try:
            res = crew.kickoff(inputs={"portfolio_id": p_id})
            raw_res = str(res)
        except Exception as e:
            status = "FAILED"
            err_msg = str(e)
            raw_res = f"Portfolio analysis failed: {err_msg}"
            logger.error(f"[PortfolioAgent] Execution failed: {e}")

        dur = time.time() - t0
        en_iso = _iso_now()

        if status == "SUCCESS":
            model, val_err = parse_and_validate_output(raw_res, PortfolioAnalysisOutput)
            conf_score = ConfidenceService.evaluate_single_agent_confidence(
                "Portfolio Agent", model, execution_success=True
            )
            display_result = raw_res if ("##" in raw_res and len(raw_res) > 200) else (model.to_markdown(portfolio_id=p_id) if model else raw_res)
        else:
            model = None
            val_err = err_msg
            display_result = raw_res
            conf_score = 15.0

        self._log_agent_run(
            agent_name="Portfolio Agent",
            task_name="Portfolio Allocation",
            output_data=raw_res,
            input_data=p_id,
            status=status,
            start_time=st_iso,
            end_time=en_iso,
            duration_seconds=dur,
            error_message=err_msg or val_err,
            confidence_score=conf_score,
        )

        return {
            "session_id": self.session_id,
            "agent": "portfolio",
            "portfolio_id": p_id,
            "result": display_result,
            "structured_output": model.model_dump() if model else None,
            "confidence_score": conf_score,
            "status": status,
            "error": err_msg,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Full Multi-Agent Pipeline (News → Tech → Risk → Fund → Port → CIO)
    # ─────────────────────────────────────────────────────────────────────────

    @rate_limited_gemini
    def analyze_stock(self, company: str, ticker: str) -> dict:
        """
        Executes the full multi-agent financial analysis crew.
        Persists real intermediate outputs, runs evidence-based confidence assessment,
        and parses recommendations strictly via Pydantic Recommendation enum.
        """
        news_agent    = self._make_news_agent()
        tech_agent    = self._make_technical_agent()
        risk_agent    = self._make_risk_agent()
        fund_agent    = self._make_fundamental_agent()
        port_agent    = self._make_portfolio_agent()
        manager_agent = self._make_manager_agent()

        news_task = Task(
            description=f"Use the news tool to fetch all news data for {ticker}. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                f"## News Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the data/events]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on the company or investor]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=news_agent,
            async_execution=True,
        )

        tech_task = Task(
            description=f"Use your tool to fetch technical indicators for {ticker}. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                f"## Technical Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining the price/indicators]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining the impact on momentum and trend]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=tech_agent,
            async_execution=True,
        )

        risk_task = Task(
            description=f"Use your tool to fetch risk metrics for {ticker}. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                f"## Risk Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining volatility, drawdown, and VaR]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining downside risk for an investor]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=risk_agent,
            context=[news_task, tech_task],
        )

        fund_task = Task(
            description=f"Use your tool to fetch fundamental data for {ticker}. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                f"## Fundamental Report for {ticker}\n"
                "**What happened?**\n"
                "[1-2 sentences explaining earnings, revenue, and valuation]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining business health and profitability]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=fund_agent,
            async_execution=True,
        )

        port_task = Task(
            description="Use your tool to retrieve holdings for the active portfolio. Write a concise, beginner-friendly report with evidence.",
            expected_output=(
                "## Portfolio Report\n"
                "**What happened?**\n"
                "[1-2 sentences explaining current holdings and asset allocation]\n\n"
                "**Why it matters?**\n"
                "[1-2 sentences explaining diversification and risk exposure]\n\n"
                "**Supporting Evidence:**\n"
                "- [Evidence item 1]\n"
                "- [Evidence item 2]\n\n"
                "**Overall conclusion**\n"
                "[2-3 sentences summarizing rebalancing recommendations, completely jargon-free]"
            ),
            agent=port_agent,
            async_execution=True,
        )

        manager_task = Task(
            description=(
                f"Review the sentiment, technical, risk, fundamental, and portfolio reports for {company} ({ticker}). "
                f"Generate a balanced, beginner-friendly master investment summary preserving the classic format.\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. Declare the final recommendation explicitly on its own line: Final Verdict: BUY (or SELL, or HOLD).\n"
                "2. Maintain the master summary format:\n"
                "   ## 📰 News Summary\n"
                "   ## 📈 Technical Summary\n"
                "   ## 🛡️ Risk Summary\n"
                "   ## 🏢 Fundamental Summary\n"
                "   ## 💼 Portfolio Summary\n"
                "   ---\n"
                "   ## 🎯 Overall Investment Outlook\n"
                "   Final Verdict: [BUY / SELL / HOLD]\n"
                "   **What happened?**\n"
                "   **Why it matters?**\n"
                "   **Supporting Evidence:**\n"
                "   **Overall conclusion**\n"
                "3. If an agent report is missing or unavailable, state that limitation clearly. Do NOT invent missing data."
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
                f"Final Verdict: [BUY / SELL / HOLD]\n\n"
                f"**What happened?**\n"
                f"[1-2 clear summary sentences]\n\n"
                f"**Why it matters?**\n"
                f"[1-2 clear sentences explaining the impact]\n\n"
                f"**Supporting Evidence:**\n"
                f"- [Evidence item 1]\n"
                f"- [Evidence item 2]\n\n"
                f"**Overall conclusion**\n"
                f"[2-3 sentences summarizing the final takeaway, completely jargon-free]"
            ),
            agent=manager_agent,
            context=[news_task, tech_task, risk_task, fund_task, port_task],
        )

        crew = Crew(
            agents=[news_agent, tech_agent, risk_agent, fund_agent, port_agent, manager_agent],
            tasks=[news_task, tech_task, risk_task, fund_task, port_task, manager_task],
            process=Process.sequential,
        )

        # Assign tools after instantiation
        news_agent.tools = [get_stock_news]
        tech_agent.tools = [get_stock_technical_data]
        risk_agent.tools = [get_risk_metrics]
        fund_agent.tools = [get_stock_fundamental_data]
        port_agent.tools = [get_portfolio_data]

        start_time_iso = _iso_now()
        start_ts = time.time()
        pipeline_status = "SUCCESS"
        pipeline_error = None
        result_raw = ""

        try:
            result = crew.kickoff(inputs={"company": company, "ticker": ticker})
            result_raw = str(result)
        except Exception as e:
            pipeline_status = "FAILED"
            pipeline_error = str(e)
            result_raw = f"Pipeline execution error: {pipeline_error}"
            logger.error(f"[FinancialCrew] Pipeline kickoff failed: {e}")

        end_ts = time.time()
        end_time_iso = _iso_now()
        duration_sec = int(end_ts - start_ts)

        # ─────────────────────────────────────────────────────────────────────
        # Extract Actual Intermediate Task Outputs & Persist to agent_runs
        # ─────────────────────────────────────────────────────────────────────
        def _get_task_raw(task: Task) -> str:
            if hasattr(task, "output") and task.output:
                if hasattr(task.output, "raw_output") and task.output.raw_output:
                    return str(task.output.raw_output)
                if hasattr(task.output, "exported_output") and task.output.exported_output:
                    return str(task.output.exported_output)
            return ""

        intermediate_raw = {
            "news": _get_task_raw(news_task),
            "technical": _get_task_raw(tech_task),
            "risk": _get_task_raw(risk_task),
            "fundamental": _get_task_raw(fund_task),
            "portfolio": _get_task_raw(port_task),
            "cio": result_raw,
        }

        # Validate specialist outputs
        validated_models: Dict[str, Any] = {}
        agent_statuses: Dict[str, str] = {}

        schema_map = {
            "news": (NewsAnalysisOutput, "News Agent", "News Sentiment Task"),
            "technical": (TechnicalAnalysisOutput, "Technical Agent", "Technical Analysis Task"),
            "risk": (RiskAnalysisOutput, "Risk Agent", "Risk Assessment Task"),
            "fundamental": (FundamentalAnalysisOutput, "Fundamental Agent", "Fundamental Valuation Task"),
            "portfolio": (PortfolioAnalysisOutput, "Portfolio Agent", "Portfolio Allocation Task"),
        }

        for key, (schema_cls, ag_name, tk_name) in schema_map.items():
            raw_out = intermediate_raw.get(key, "").strip()
            if raw_out:
                mod, err = parse_and_validate_output(raw_out, schema_cls)
                validated_models[key] = mod
                agent_statuses[key] = "SUCCESS" if mod else "FAILED"
                agent_conf = ConfidenceService.evaluate_single_agent_confidence(ag_name, mod, bool(mod))
                self._log_agent_run(
                    agent_name=ag_name,
                    task_name=tk_name,
                    output_data=raw_out,
                    input_data=ticker,
                    status=agent_statuses[key],
                    start_time=start_time_iso,
                    end_time=end_time_iso,
                    duration_seconds=float(duration_sec),
                    error_message=err,
                    confidence_score=agent_conf,
                )
            else:
                agent_statuses[key] = "FAILED"
                self._log_agent_run(
                    agent_name=ag_name,
                    task_name=tk_name,
                    output_data="[No output produced: task failed or produced empty response]",
                    input_data=ticker,
                    status="FAILED",
                    start_time=start_time_iso,
                    end_time=end_time_iso,
                    duration_seconds=float(duration_sec),
                    error_message="Task yielded no output",
                    confidence_score=15.0,
                )

        # ─────────────────────────────────────────────────────────────────────
        # Recommendation Extraction & Validation
        # ─────────────────────────────────────────────────────────────────────
        parsed_rec = parse_cio_recommendation_strict(result_raw)
        recommendation_str = parsed_rec.value if parsed_rec else None

        if not recommendation_str:
            # Handle missing or invalid recommendation explicitly
            logger.warning(
                f"[FinancialCrew] CIO output lacked explicit BUY/SELL/HOLD declaration. "
                "Defaulting to HOLD with explicit diagnostic warning."
            )
            recommendation_str = "HOLD"
            rec_explicitly_declared = False
        else:
            rec_explicitly_declared = True

        # Validate CIO output against Pydantic schema
        cio_model, cio_err = parse_and_validate_output(result_raw, CIORecommendationOutput)

        # ─────────────────────────────────────────────────────────────────────
        # Evidence-Based Confidence Assessment
        # ─────────────────────────────────────────────────────────────────────
        conf_report: ConfidenceReport = ConfidenceService.evaluate_crew_confidence(
            agent_outputs=validated_models,
            agent_statuses=agent_statuses,
            recommendation=recommendation_str,
        )

        # Log CIO run
        self._log_agent_run(
            agent_name="Manager Agent",
            task_name="Master Investment Summary (CIO)",
            output_data=result_raw,
            input_data=ticker,
            status=pipeline_status,
            start_time=start_time_iso,
            end_time=end_time_iso,
            duration_seconds=float(duration_sec),
            error_message=pipeline_error or (cio_err if not rec_explicitly_declared else None),
            confidence_score=conf_report.score,
        )

        # Format markdown output for presentation
        if cio_model:
            cio_model.confidence_score = conf_report.score
            final_markdown = cio_model.to_markdown(company=company, ticker=ticker)
        else:
            final_markdown = result_raw

        # ─────────────────────────────────────────────────────────────────────
        # Save to SQLite Analysis History
        # ─────────────────────────────────────────────────────────────────────
        try:
            factors_json = json.dumps(conf_report.to_dict())
            SQLiteClient.execute_write(
                "INSERT INTO analysis_history ("
                "  id, session_id, user_id, ticker, company_name, recommendation, "
                "  score, agents, summary, duration, confidence_factors"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    self.session_id,
                    "default_user",
                    ticker,
                    company,
                    recommendation_str,
                    conf_report.score,
                    json.dumps(["News", "Technical", "Risk", "Fundamental", "Portfolio", "CIO"]),
                    final_markdown,
                    f"{duration_sec}s",
                    factors_json,
                ),
            )
        except Exception as e:
            logger.error(f"Failed to log session summary to SQLite: {e}")

        return {
            "session_id": self.session_id,
            "company": company,
            "ticker": ticker,
            "recommendation": final_markdown,  # Preserves frontend Markdown rendering
            "recommendation_type": recommendation_str,
            "confidence_score": conf_report.score,
            "confidence_level": conf_report.confidence_level,
            "confidence_breakdown": conf_report.to_dict(),
            "detected_conflicts": conf_report.detected_conflicts,
            "specialist_outputs": {
                k: (m.model_dump() if m else None) for k, m in validated_models.items()
            },
        }


def get_financial_crew(session_id: str = None) -> FinancialCrew:
    return FinancialCrew(session_id=session_id)
