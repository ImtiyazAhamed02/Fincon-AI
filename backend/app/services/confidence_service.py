"""
app/services/confidence_service.py
─────────────────────────────────────────────────────────────────────────────
Evidence-Based Confidence Assessment Engine for FINCON Multi-Agent System
─────────────────────────────────────────────────────────────────────────────

Calculates an objective, deterministic confidence score (0-100) reflecting
the rigor, completeness, and coherence of the financial analysis.

Distinguishes analysis reliability from directional market probability.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ConfidenceReport:
    score: float
    confidence_level: str  # HIGH, MODERATE, LOW, INSUFFICIENT_DATA
    factors: Dict[str, Any]
    detected_conflicts: List[str]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConfidenceService:
    """
    Evidence-based confidence scoring engine.
    
    Formula:
      Total Score (0-100) = Completeness (max 35)
                          + Data Quality & Freshness (max 25)
                          + Signal Coherence (max 25)
                          + Depth & Detail (max 15)
    """

    CORE_AGENTS = ["news", "technical", "risk", "fundamental", "portfolio"]

    @classmethod
    def evaluate_crew_confidence(
        cls,
        agent_outputs: Dict[str, Any],
        agent_statuses: Dict[str, str],
        recommendation: Optional[str] = None
    ) -> ConfidenceReport:
        """
        Calculates confidence for the entire multi-agent session.
        """
        # 1. Completeness Score (max 35)
        successful_agents = [
            agent for agent in cls.CORE_AGENTS
            if agent_statuses.get(agent) == "SUCCESS" and agent_outputs.get(agent)
        ]
        completeness_score = len(successful_agents) * 7.0  # 5 * 7 = 35 max

        # 2. Data Quality & Freshness Score (max 25)
        quality_score = 0.0
        data_checks = {}

        # Technical data presence
        tech_data = agent_outputs.get("technical")
        has_tech = False
        if tech_data:
            has_tech = bool(
                getattr(tech_data, "rsi_14", None) is not None
                or getattr(tech_data, "trend_bias", None) in ("BULLISH", "BEARISH", "NEUTRAL")
                or (isinstance(tech_data, dict) and tech_data.get("trend_bias"))
            )
        data_checks["technical_indicators_verified"] = has_tech
        if has_tech:
            quality_score += 8.0

        # News freshness presence
        news_data = agent_outputs.get("news")
        has_news = False
        if news_data:
            headlines_count = getattr(news_data, "relevant_headlines_count", 0)
            if isinstance(news_data, dict):
                headlines_count = news_data.get("relevant_headlines_count", 0)
            has_news = bool(headlines_count > 0 or getattr(news_data, "sentiment", None) or (isinstance(news_data, dict) and news_data.get("sentiment")))
        data_checks["news_sentiment_grounded"] = has_news
        if has_news:
            quality_score += 8.0

        # Risk metrics presence
        risk_data = agent_outputs.get("risk")
        has_risk = False
        if risk_data:
            has_risk = bool(
                getattr(risk_data, "risk_level", None)
                or getattr(risk_data, "annualized_volatility", None) is not None
                or (isinstance(risk_data, dict) and (risk_data.get("risk_level") or risk_data.get("annualized_volatility")))
            )
        data_checks["risk_metrics_calculated"] = has_risk
        if has_risk:
            quality_score += 5.0

        # Fundamental metrics presence
        fund_data = agent_outputs.get("fundamental")
        has_fund = False
        if fund_data:
            has_fund = bool(
                getattr(fund_data, "valuation_assessment", None)
                or getattr(fund_data, "pe_ratio", None) is not None
                or (isinstance(fund_data, dict) and (fund_data.get("valuation_assessment") or fund_data.get("pe_ratio")))
            )
        data_checks["fundamentals_present"] = has_fund
        if has_fund:
            quality_score += 4.0

        # 3. Signal Coherence & Conflict Penalty (max 25)
        coherence_score = 25.0
        conflicts = []

        # Extract sentiments / biases
        def _get_val(obj, attr, default=None):
            if hasattr(obj, attr):
                return getattr(obj, attr)
            if isinstance(obj, dict):
                return obj.get(attr)
            return default

        news_sent = (_get_val(news_data, "sentiment") or "").upper()
        tech_bias = (_get_val(tech_data, "trend_bias") or "").upper()
        risk_lvl = (_get_val(risk_data, "risk_level") or "").upper()
        fund_val = (_get_val(fund_data, "valuation_assessment") or "").upper()

        # Check Conflict: News Bullish vs Tech Bearish (or vice-versa)
        if ("BULLISH" in news_sent and "BEARISH" in tech_bias) or ("BEARISH" in news_sent and "BULLISH" in tech_bias):
            conflict_msg = f"Sentiment/Technical divergence: News is {news_sent} while Technicals indicate {tech_bias}."
            conflicts.append(conflict_msg)
            coherence_score -= 8.0

        # Check Conflict: High Risk vs BUY recommendation
        if recommendation and recommendation.upper() == "BUY" and risk_lvl in ("HIGH", "EXTREME"):
            conflict_msg = f"Risk/Recommendation tension: Overall recommendation is BUY despite {risk_lvl} risk assessment."
            conflicts.append(conflict_msg)
            coherence_score -= 8.0

        # Check Conflict: Overvalued Fundamentals vs BUY
        if recommendation and recommendation.upper() == "BUY" and "OVERVALUED" in fund_val:
            conflict_msg = "Fundamental tension: Recommendation is BUY while valuation is assessed as OVERVALUED."
            conflicts.append(conflict_msg)
            coherence_score -= 5.0

        coherence_score = max(0.0, coherence_score)

        # 4. Depth & Analytical Detail (max 15)
        depth_score = 0.0
        for agent in cls.CORE_AGENTS:
            out = agent_outputs.get(agent)
            if not out:
                continue
            findings = _get_val(out, "key_findings", [])
            evidence = _get_val(out, "supporting_evidence", [])
            if len(findings) >= 2 or len(evidence) >= 1:
                depth_score += 3.0
        depth_score = min(15.0, depth_score)

        # Total Calculation
        total = round(completeness_score + quality_score + coherence_score + depth_score, 1)
        total = min(100.0, max(0.0, total))

        if total >= 75.0:
            level = "HIGH"
        elif total >= 50.0:
            level = "MODERATE"
        elif total >= 30.0:
            level = "LOW"
        else:
            level = "INSUFFICIENT_DATA"

        notes = f"Assessed across {len(successful_agents)}/{len(cls.CORE_AGENTS)} specialist agents."
        if conflicts:
            notes += f" Detected {len(conflicts)} signal conflict(s)."

        factors = {
            "completeness": {
                "score": completeness_score,
                "max": 35.0,
                "successful_agents": successful_agents,
                "failed_or_missing_agents": [a for a in cls.CORE_AGENTS if a not in successful_agents],
            },
            "data_quality_and_freshness": {
                "score": quality_score,
                "max": 25.0,
                "details": data_checks,
            },
            "signal_coherence": {
                "score": coherence_score,
                "max": 25.0,
                "conflicts": conflicts,
            },
            "depth_and_detail": {
                "score": depth_score,
                "max": 15.0,
            },
        }

        return ConfidenceReport(
            score=total,
            confidence_level=level,
            factors=factors,
            detected_conflicts=conflicts,
            notes=notes,
        )

    @classmethod
    def evaluate_single_agent_confidence(
        cls,
        agent_name: str,
        structured_output: Any,
        execution_success: bool = True
    ) -> float:
        """
        Calculates an evidence-based confidence score (0-100) for a single agent run.
        """
        if not execution_success or not structured_output:
            return 15.0  # Minimal confidence for failed or empty run

        score = 50.0  # Base for successful run

        def _get(attr, default=None):
            if hasattr(structured_output, attr):
                return getattr(structured_output, attr)
            if isinstance(structured_output, dict):
                return structured_output.get(attr, default)
            return default

        findings = _get("key_findings", [])
        evidence = _get("supporting_evidence", [])
        risks = _get("risks", [])

        # Evidence depth bonus
        if len(findings) >= 2:
            score += 15.0
        elif len(findings) >= 1:
            score += 8.0

        if len(evidence) >= 2:
            score += 15.0
        elif len(evidence) >= 1:
            score += 8.0

        if len(risks) >= 1:
            score += 10.0

        return min(95.0, max(20.0, round(score, 1)))
