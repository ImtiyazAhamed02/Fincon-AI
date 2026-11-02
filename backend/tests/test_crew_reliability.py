"""
backend/tests/test_crew_reliability.py
─────────────────────────────────────────────────────────────────────────────
Comprehensive Unit Tests for FINCON Multi-Agent Output Reliability,
Recommendation Parsing, Confidence Scoring & Logging.

All LLM and external calls are mocked so no network or paid API tokens are used.
─────────────────────────────────────────────────────────────────────────────
"""

import sys
import os

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
import uuid
import json
from unittest.mock import MagicMock, patch

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
from app.agents.crew import FinancialCrew
from app.db.client import SQLiteClient, init_db


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is initialized and migrated before tests run."""
    init_db()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Valid BUY recommendation
# ─────────────────────────────────────────────────────────────────────────────
def test_valid_buy_recommendation():
    sample_cio_output = (
        "# Master Investment Summary for Apple (AAPL)\n\n"
        "### 🎯 Final Verdict: BUY\n"
        "**Analysis Confidence**: 88.5%\n\n"
        "## 📋 Executive Summary\n"
        "Strong fundamentals and robust momentum indicate upward trajectory.\n\n"
        "## 🔍 Key Findings\n"
        "- Revenue expanded 12% YoY.\n"
        "- RSI remains healthy at 54.\n\n"
        "## 📊 Supporting Evidence\n"
        "- Recent product launches beating expectations.\n\n"
        "## 🛡️ Downside Risks\n"
        "- Global trade volatility.\n"
    )

    rec = parse_cio_recommendation_strict(sample_cio_output)
    assert rec == Recommendation.BUY

    model, err = parse_and_validate_output(sample_cio_output, CIORecommendationOutput)
    assert err is None
    assert model is not None
    assert model.recommendation == Recommendation.BUY
    assert len(model.key_findings) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Valid SELL recommendation
# ─────────────────────────────────────────────────────────────────────────────
def test_valid_sell_recommendation():
    sample_cio_output = (
        "# Master Investment Summary for Overvalued Corp (OVC)\n\n"
        "Recommendation: SELL\n\n"
        "## 📋 Executive Summary\n"
        "Deteriorating cash flows and bearish breakdown.\n\n"
        "## 🔍 Key Findings\n"
        "- Negative operating margin contraction.\n"
        "- Support broken at $140.\n\n"
        "## 📊 Supporting Evidence\n"
        "- Multiple analyst downgrades.\n\n"
        "## 🛡️ Downside Risks\n"
        "- Liquidity crunch.\n"
    )

    rec = parse_cio_recommendation_strict(sample_cio_output)
    assert rec == Recommendation.SELL

    model, err = parse_and_validate_output(sample_cio_output, CIORecommendationOutput)
    assert err is None
    assert model is not None
    assert model.recommendation == Recommendation.SELL


# ─────────────────────────────────────────────────────────────────────────────
# 3. Valid HOLD recommendation
# ─────────────────────────────────────────────────────────────────────────────
def test_valid_hold_recommendation():
    sample_cio_output = (
        "# Master Investment Summary for Stable Utilities (SUT)\n\n"
        "Verdict: HOLD\n\n"
        "## 📋 Executive Summary\n"
        "Fairly valued with balanced risk profile.\n\n"
        "## 🔍 Key Findings\n"
        "- Dividend yields stable.\n"
        "- Low volatility across trading periods.\n\n"
        "## 📊 Supporting Evidence\n"
        "- Steady utility revenue streams.\n\n"
        "## 🛡️ Downside Risks\n"
        "- Rising bond yield competition.\n"
    )

    rec = parse_cio_recommendation_strict(sample_cio_output)
    assert rec == Recommendation.HOLD

    model, err = parse_and_validate_output(sample_cio_output, CIORecommendationOutput)
    assert err is None
    assert model is not None
    assert model.recommendation == Recommendation.HOLD


# ─────────────────────────────────────────────────────────────────────────────
# 4. Missing or malformed recommendation
# ─────────────────────────────────────────────────────────────────────────────
def test_missing_or_malformed_recommendation():
    # Report that gives analysis but omits the explicit recommendation header
    malformed_output = (
        "# Master Investment Summary for Mystery Corp (MC)\n\n"
        "## 📋 Executive Summary\n"
        "The market has mixed signals. Some people speculate on upside, others on downside.\n\n"
        "## 🔍 Key Findings\n"
        "- Unclear path forward.\n"
    )

    rec = parse_cio_recommendation_strict(malformed_output)
    assert rec is None  # Must NOT guess BUY or SELL

    model, err = parse_and_validate_output(malformed_output, CIORecommendationOutput)
    assert model is None
    assert "Malformed or missing recommendation" in err


# ─────────────────────────────────────────────────────────────────────────────
# 5. Conflicting BUY and SELL keywords in report text
# ─────────────────────────────────────────────────────────────────────────────
def test_conflicting_keywords_in_report_text():
    # In the old code: if "BUY" in res_str: rec = "BUY"
    # This report contains the word "BUY" but explicitly declares a SELL verdict!
    tricky_report = (
        "# Master Investment Summary\n\n"
        "Do NOT buy this stock under any circumstances. Even if bullish investors "
        "advocate to buy dips, we strongly advise against buying.\n\n"
        "Recommendation: SELL\n\n"
        "## 📋 Executive Summary\n"
        "Technicals broke key support and insider selling accelerated.\n\n"
        "## 🔍 Key Findings\n"
        "- Heavy selling pressure.\n"
    )

    # Substring search would wrongly find "BUY" first
    assert "BUY" in tricky_report.upper()

    # Strict parser must correctly extract SELL
    rec = parse_cio_recommendation_strict(tricky_report)
    assert rec == Recommendation.SELL
    assert rec != Recommendation.BUY


# ─────────────────────────────────────────────────────────────────────────────
# 6. Missing agent output
# ─────────────────────────────────────────────────────────────────────────────
def test_missing_agent_output():
    # One or more agents fail or yield empty output
    empty_raw = ""
    model, err = parse_and_validate_output(empty_raw, NewsAnalysisOutput)
    assert model is None
    assert "Empty agent response" in err

    # Confidence engine penalizes missing agents
    report = ConfidenceService.evaluate_crew_confidence(
        agent_outputs={},
        agent_statuses={
            "news": "FAILED",
            "technical": "FAILED",
            "risk": "FAILED",
            "fundamental": "FAILED",
            "portfolio": "FAILED",
        },
        recommendation="HOLD"
    )
    # Score should be very low due to zero completeness
    assert report.score < 30.0
    assert report.confidence_level == "INSUFFICIENT_DATA"
    assert "failed_or_missing_agents" in report.factors["completeness"]


# ─────────────────────────────────────────────────────────────────────────────
# 7. Failed agent execution
# ─────────────────────────────────────────────────────────────────────────────
def test_failed_agent_execution_logging():
    session_id = f"test-fail-{uuid.uuid4()}"
    crew = FinancialCrew(session_id=session_id)

    # Log a failed agent run
    crew._log_agent_run(
        agent_name="Risk Agent",
        task_name="Risk Assessment",
        output_data="[No output produced: task failed]",
        input_data="FAIL",
        status="FAILED",
        duration_seconds=1.25,
        error_message="Yahoo Finance API Timeout after 30s",
        confidence_score=15.0,
    )

    rows = SQLiteClient.execute(
        "SELECT agent_name, status, error_message, confidence_score FROM agent_runs WHERE session_id = ?",
        (session_id,)
    )
    assert len(rows) == 1
    assert rows[0]["status"] == "FAILED"
    assert "Timeout" in rows[0]["error_message"]
    assert rows[0]["confidence_score"] == 15.0


# ─────────────────────────────────────────────────────────────────────────────
# 8. Successful intermediate output persistence
# ─────────────────────────────────────────────────────────────────────────────
def test_successful_intermediate_output_persistence():
    session_id = f"test-persist-{uuid.uuid4()}"
    crew = FinancialCrew(session_id=session_id)

    actual_news_output = "## News Report for AAPL\n**Sentiment**: BULLISH\nAnalyzed 12 articles."
    actual_tech_output = "## Technical Report for AAPL\n**Technical Bias**: BULLISH\nRSI is 58.2."

    crew._log_agent_run(
        agent_name="News Agent",
        task_name="News Sentiment Task",
        output_data=actual_news_output,
        input_data="AAPL",
        status="SUCCESS",
        start_time="2026-11-02 12:00:00 UTC",
        end_time="2026-11-02 12:00:04 UTC",
        duration_seconds=4.12,
        confidence_score=85.0,
    )

    crew._log_agent_run(
        agent_name="Technical Agent",
        task_name="Technical Analysis Task",
        output_data=actual_tech_output,
        input_data="AAPL",
        status="SUCCESS",
        start_time="2026-11-02 12:00:04 UTC",
        end_time="2026-11-02 12:00:08 UTC",
        duration_seconds=3.95,
        confidence_score=88.0,
    )

    rows = SQLiteClient.execute(
        "SELECT agent_name, output_data, status, duration_seconds FROM agent_runs WHERE session_id = ? ORDER BY start_time ASC",
        (session_id,)
    )
    assert len(rows) == 2
    # Verify ACTUAL outputs are stored instead of dummy "Executed News Task" strings
    assert "Analyzed 12 articles" in rows[0]["output_data"]
    assert "Executed News Task" not in rows[0]["output_data"]
    assert "RSI is 58.2" in rows[1]["output_data"]
    assert rows[0]["status"] == "SUCCESS"
    assert rows[0]["duration_seconds"] == 4.12


# ─────────────────────────────────────────────────────────────────────────────
# 9. Confidence calculation with complete evidence
# ─────────────────────────────────────────────────────────────────────────────
def test_confidence_calculation_complete_evidence():
    news_out = NewsAnalysisOutput(
        summary="Positive quarterly earnings beating consensus.",
        key_findings=["Revenue up 15%", "Margins expanding"],
        supporting_evidence=["SEC 10-Q filing", "Bloomberg consensus beat"],
        risks=["FX currency headwind"],
        sentiment="BULLISH",
        relevant_headlines_count=8,
    )

    tech_out = TechnicalAnalysisOutput(
        summary="Bullish continuation pattern above 50-day moving average.",
        key_findings=["Breakout above resistance at $180", "MACD histogram expanding"],
        supporting_evidence=["Volume 1.4x 30-day average"],
        risks=["Overbought short-term RSI"],
        trend_bias="BULLISH",
        rsi_14=62.5,
        macd_signal="BULLISH_CROSSOVER",
    )

    risk_out = RiskAnalysisOutput(
        summary="Moderate volatility with contained downside risk.",
        key_findings=["Beta of 1.05", "Drawdown within historical tolerances"],
        supporting_evidence=["95% VaR at -2.4%"],
        risks=["Broad equity market correction"],
        risk_level="MODERATE",
        annualized_volatility=18.5,
        var_95=2.4,
    )

    fund_out = FundamentalAnalysisOutput(
        summary="Healthy balance sheet with net cash position.",
        key_findings=["P/E ratio fair at 24.5", "Free cash flow yield 4.2%"],
        supporting_evidence=["Q3 cash flow statement"],
        risks=["Competition in core market"],
        valuation_assessment="FAIR",
        pe_ratio=24.5,
    )

    port_out = PortfolioAnalysisOutput(
        summary="Portfolio maintains balanced exposure.",
        key_findings=["Stock accounts for 4.5% of total portfolio", "Diversification score high"],
        supporting_evidence=["Portfolio holdings registry"],
        risks=["Slight technology sector tilt"],
        allocation_status="BALANCED",
    )

    report = ConfidenceService.evaluate_crew_confidence(
        agent_outputs={
            "news": news_out,
            "technical": tech_out,
            "risk": risk_out,
            "fundamental": fund_out,
            "portfolio": port_out,
        },
        agent_statuses={
            "news": "SUCCESS",
            "technical": "SUCCESS",
            "risk": "SUCCESS",
            "fundamental": "SUCCESS",
            "portfolio": "SUCCESS",
        },
        recommendation="BUY"
    )

    # All 5 agents succeeded, indicators verified, coherent signals
    assert report.score >= 85.0
    assert report.confidence_level == "HIGH"
    assert len(report.detected_conflicts) == 0
    assert report.factors["completeness"]["score"] == 35.0
    assert report.factors["data_quality_and_freshness"]["score"] == 25.0


# ─────────────────────────────────────────────────────────────────────────────
# 10. Confidence calculation with incomplete or conflicting evidence
# ─────────────────────────────────────────────────────────────────────────────
def test_confidence_calculation_conflicting_evidence():
    # Conflicting setup: News is strongly BEARISH, Technical is BULLISH, Risk is HIGH,
    # yet recommendation is BUY!
    news_out = NewsAnalysisOutput(
        summary="Regulator opens antitrust investigation.",
        key_findings=["Subpoenas issued", "Significant fines possible"],
        supporting_evidence=["DOJ Press Release"],
        risks=["Regulatory sanction"],
        sentiment="BEARISH",
        relevant_headlines_count=5,
    )

    tech_out = TechnicalAnalysisOutput(
        summary="Short term momentum surge.",
        key_findings=["RSI reaching 78", "Spike on high volume"],
        supporting_evidence=["Technical indicators"],
        risks=["Overextended"],
        trend_bias="BULLISH",
        rsi_14=78.0,
    )

    risk_out = RiskAnalysisOutput(
        summary="Severe volatility due to legal uncertainty.",
        key_findings=["VaR elevated", "Beta exceeding 2.2"],
        supporting_evidence=["Historical litigation volatility"],
        risks=["Severe tail risk"],
        risk_level="HIGH",
        annualized_volatility=48.0,
    )

    report = ConfidenceService.evaluate_crew_confidence(
        agent_outputs={
            "news": news_out,
            "technical": tech_out,
            "risk": risk_out,
            # fundamental and portfolio missing!
        },
        agent_statuses={
            "news": "SUCCESS",
            "technical": "SUCCESS",
            "risk": "SUCCESS",
            "fundamental": "FAILED",
            "portfolio": "FAILED",
        },
        recommendation="BUY"
    )

    # Completeness is penalized (only 3 agents = 21 points max instead of 35)
    assert report.factors["completeness"]["score"] == 21.0

    # Conflicting signals detected
    assert len(report.detected_conflicts) >= 2
    # News Bearish vs Tech Bullish
    assert any("divergence" in c.lower() for c in report.detected_conflicts)
    # High Risk vs BUY recommendation
    assert any("risk/recommendation" in c.lower() for c in report.detected_conflicts)

    # Total score should be substantially lower than complete evidence
    assert report.score < 65.0
    assert report.confidence_level in ("MODERATE", "LOW")


# ─────────────────────────────────────────────────────────────────────────────
# 11. Groq tool_use_failed auto-recovery into CrewAI ReAct action
# ─────────────────────────────────────────────────────────────────────────────
def test_groq_tool_use_failed_recovery():
    from app.services.ai.smart_llm import SmartLLM

    # Exact error payload returned by Groq when model calls a tool without tools payload
    groq_err_msg = (
        "Error code: 400 - {'error': {'message': 'Tool choice is none, but model called a tool', "
        "'type': 'invalid_request_error', 'code': 'tool_use_failed', "
        "'failed_generation': '{\"name\": \"get_stock_fundamental_data\", \"arguments\": {\"ticker\":\"TCS\"}}'}}"
    )
    res = SmartLLM._recover_groq_tool_call(Exception(groq_err_msg))
    assert res is not None
    assert len(res.generations) > 0
    content = res.generations[0].message.content
    assert "Action: get_stock_fundamental_data" in content
    assert '"ticker": "TCS"' in content
    assert "Thought:" in content
