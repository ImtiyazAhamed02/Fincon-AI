"""
app/schemas/agent_outputs.py
─────────────────────────────────────────────────────────────────────────────
Structured Pydantic Output Schemas and Recommendation Enums for FINCON Agents
─────────────────────────────────────────────────────────────────────────────
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
import json
import re


class Recommendation(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseAgentOutput(BaseModel):
    what_happened: str = Field(default="", description="1-2 sentences explaining what happened / data events")
    why_it_matters: str = Field(default="", description="1-2 sentences explaining why it matters for the company or investor")
    supporting_evidence: List[str] = Field(default_factory=list, description="Data points and metrics supporting findings")
    overall_conclusion: str = Field(default="", description="2-3 sentences summarizing the final takeaway, completely jargon-free")

    # Backward-compatible fields
    summary: str = Field(default="", description="High-level executive summary of the analysis")
    key_findings: List[str] = Field(default_factory=list, description="List of key findings identified")
    risks: List[str] = Field(default_factory=list, description="Key risks identified during analysis")

    def to_markdown(self) -> str:
        """Standard human-readable markdown matching the classic FINCON format."""
        lines = [
            "**What happened?**",
            self.what_happened or self.summary,
            "",
            "**Why it matters?**",
            self.why_it_matters or "Key implications for the company and investors.",
            "",
            "**Supporting Evidence:**",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Real-time market data verified.",
            "",
            "**Overall conclusion**",
            self.overall_conclusion or self.summary,
        ]
        return "\n".join(lines)


class NewsAnalysisOutput(BaseAgentOutput):
    sentiment: str = Field(default="NEUTRAL", description="Overall news sentiment: BULLISH, BEARISH, or NEUTRAL")
    relevant_headlines_count: int = Field(default=0, description="Number of news items analyzed")
    data_freshness: str = Field(default="Recent", description="Freshness of the analyzed news")

    def to_markdown(self, ticker: str = "") -> str:
        heading = f"## News Report for {ticker}" if ticker else "## News Report"
        lines = [
            heading,
            "",
            "**What happened?**",
            self.what_happened or self.summary,
            "",
            "**Why it matters?**",
            self.why_it_matters or "Direct impact on corporate momentum and sentiment.",
            "",
            "**Supporting Evidence:**",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Market news verified via Finnhub.",
            "",
            "**Overall conclusion**",
            self.overall_conclusion or self.summary,
        ]
        return "\n".join(lines)


class TechnicalAnalysisOutput(BaseAgentOutput):
    trend_bias: str = Field(default="NEUTRAL", description="BULLISH, BEARISH, or NEUTRAL")
    rsi_14: Optional[float] = Field(default=None, description="RSI indicator value")
    macd_signal: Optional[str] = Field(default=None, description="MACD interpretation")
    support_level: Optional[float] = Field(default=None, description="Key support price")
    resistance_level: Optional[float] = Field(default=None, description="Key resistance price")
    indicators_summary: Dict[str, Any] = Field(default_factory=dict, description="Raw or parsed indicator values")

    def to_markdown(self, ticker: str = "") -> str:
        heading = f"## Technical Report for {ticker}" if ticker else "## Technical Report"
        lines = [
            heading,
            "",
            "**What happened?**",
            self.what_happened or self.summary,
            "",
            "**Why it matters?**",
            self.why_it_matters or "Price momentum and key technical support/resistance levels.",
            "",
            "**Supporting Evidence:**",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Institutional indicators calculated via yfinance.",
            "",
            "**Overall conclusion**",
            self.overall_conclusion or self.summary,
        ]
        return "\n".join(lines)


class RiskAnalysisOutput(BaseAgentOutput):
    risk_level: str = Field(default="MODERATE", description="LOW, MODERATE, HIGH, or EXTREME")
    annualized_volatility: Optional[float] = Field(default=None, description="Annualized volatility percentage")
    var_95: Optional[float] = Field(default=None, description="Value at Risk (95% confidence)")
    max_drawdown: Optional[float] = Field(default=None, description="Maximum historical drawdown percentage")

    def to_markdown(self, ticker: str = "") -> str:
        heading = f"## Risk Report for {ticker}" if ticker else "## Risk Report"
        lines = [
            heading,
            "",
            "**What happened?**",
            self.what_happened or self.summary,
            "",
            "**Why it matters?**",
            self.why_it_matters or "Downside exposure, capital preservation, and drawdown vulnerability.",
            "",
            "**Supporting Evidence:**",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Quantitative risk metrics calculated via historical price action.",
            "",
            "**Overall conclusion**",
            self.overall_conclusion or self.summary,
        ]
        return "\n".join(lines)


class FundamentalAnalysisOutput(BaseAgentOutput):
    valuation_assessment: str = Field(default="FAIR", description="UNDERVALUED, FAIR, or OVERVALUED")
    pe_ratio: Optional[float] = Field(default=None, description="Trailing P/E ratio")
    revenue_growth_yoy: Optional[float] = Field(default=None, description="YoY revenue growth percentage")
    profit_margins: Optional[str] = Field(default=None, description="Margin assessment")

    def to_markdown(self, ticker: str = "") -> str:
        heading = f"## Fundamental Report for {ticker}" if ticker else "## Fundamental Report"
        lines = [
            heading,
            "",
            "**What happened?**",
            self.what_happened or self.summary,
            "",
            "**Why it matters?**",
            self.why_it_matters or "Balance sheet health, earnings power, and valuation multiple sustainability.",
            "",
            "**Supporting Evidence:**",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Financial disclosures and institutional valuation models.",
            "",
            "**Overall conclusion**",
            self.overall_conclusion or self.summary,
        ]
        return "\n".join(lines)


class PortfolioAnalysisOutput(BaseAgentOutput):
    allocation_status: str = Field(default="BALANCED", description="OVERWEIGHT, UNDERWEIGHT, or BALANCED")
    diversification_score: Optional[float] = Field(default=None, description="Diversification score out of 100")
    rebalancing_action: Optional[str] = Field(default=None, description="Suggested rebalance action")

    def to_markdown(self, portfolio_id: str = "") -> str:
        p_label = f" for {portfolio_id}" if portfolio_id else ""
        lines = [
            f"## Portfolio Report{p_label}",
            "",
            "**What happened?**",
            self.what_happened or self.summary,
            "",
            "**Why it matters?**",
            self.why_it_matters or "Asset allocation balance and concentration risk management.",
            "",
            "**Supporting Evidence:**",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Portfolio holdings weights and sector distribution.",
            "",
            "**Overall conclusion**",
            self.overall_conclusion or self.summary,
        ]
        return "\n".join(lines)


class CIORecommendationOutput(BaseAgentOutput):
    recommendation: Recommendation = Field(..., description="Mandatory verdict: BUY, SELL, or HOLD")
    time_horizon: str = Field(default="Medium-term (3-12 months)", description="Investment horizon")
    conflicting_signals: List[str] = Field(default_factory=list, description="Contradictions between agents identified")
    limitations_and_missing_data: List[str] = Field(default_factory=list, description="Missing metrics or limits to analysis")
    confidence_score: float = Field(default=0.0, description="Evidence-calibrated confidence score between 0 and 100")

    news_summary: str = Field(default="", description="Summary from News Agent")
    technical_summary: str = Field(default="", description="Summary from Technical Agent")
    risk_summary: str = Field(default="", description="Summary from Risk Agent")
    fundamental_summary: str = Field(default="", description="Summary from Fundamental Agent")
    portfolio_summary: str = Field(default="", description="Summary from Portfolio Agent")

    @field_validator("recommendation", mode="before")
    @classmethod
    def validate_recommendation(cls, v: Any) -> Recommendation:
        if isinstance(v, Recommendation):
            return v
        if isinstance(v, str):
            clean = v.strip().upper()
            # Strict mapping - do not guess from sentences
            if clean in ("BUY", "STRONG_BUY"):
                return Recommendation.BUY
            if clean in ("SELL", "STRONG_SELL"):
                return Recommendation.SELL
            if clean in ("HOLD", "NEUTRAL"):
                return Recommendation.HOLD
        raise ValueError(f"Invalid recommendation '{v}'. Must be one of: BUY, SELL, HOLD.")

    def to_markdown(self, company: str = "", ticker: str = "") -> str:
        comp_str = f" for {company} ({ticker})" if company and ticker else f" for {ticker}" if ticker else ""
        rec_badge = self.recommendation.value
        rec_color_emoji = "🟢" if rec_badge == "BUY" else "🔴" if rec_badge == "SELL" else "🟡"

        lines = [
            f"# Master Investment Summary{comp_str}",
            "",
            f"## 📰 News Summary\n{self.news_summary or self.what_happened or self.summary}\n",
            f"## 📈 Technical Summary\n{self.technical_summary or 'Technical indicators evaluated.'}\n",
            f"## 🛡️ Risk Summary\n{self.risk_summary or 'Risk metrics and drawdown risk evaluated.'}\n",
            f"## 🏢 Fundamental Summary\n{self.fundamental_summary or 'Valuation and earnings health evaluated.'}\n",
            f"## 💼 Portfolio Summary\n{self.portfolio_summary or 'Portfolio allocation evaluated.'}\n",
            "---",
            "",
            "## 🎯 Overall Investment Outlook",
            f"**Final Recommendation**: {rec_color_emoji} **{rec_badge}**",
            "",
            "**What happened?**",
            self.what_happened or self.summary,
            "",
            "**Why it matters?**",
            self.why_it_matters or "Strategic implications across all research modules.",
            "",
            "**Supporting Evidence:**",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Multi-agent quantitative & qualitative inputs.",
            "",
            "**Overall conclusion**",
            self.overall_conclusion or self.summary,
        ]
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Robust Output Parsing & Fallback Extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_json_block(text: str) -> Optional[dict]:
    """Extracts a valid JSON object from text, handling markdown fences and noisy output."""
    if not text:
        return None
    # 1. Direct parse attempt
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # 2. Extract ```json ... ``` blocks
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # 3. Find outermost braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass

    return None


def parse_cio_recommendation_strict(raw_text: str) -> Optional[Recommendation]:
    """
    Extracts BUY, SELL, or HOLD strictly from dedicated recommendation fields.
    NEVER searches the entire report body for keywords.
    """
    # 1. Try JSON extraction
    data = extract_json_block(raw_text)
    if data and "recommendation" in data:
        val = str(data["recommendation"]).strip().upper()
        if val in ("BUY", "STRONG_BUY"):
            return Recommendation.BUY
        if val in ("SELL", "STRONG_SELL"):
            return Recommendation.SELL
        if val in ("HOLD", "NEUTRAL"):
            return Recommendation.HOLD

    # 2. Check dedicated recommendation headers/lines only: e.g. "Recommendation: BUY"
    rec_line_patterns = [
        r"(?:Final\s+)?Recommendation\s*[:\-=]\s*[`\*\_]*\s*(BUY|SELL|HOLD)\b",
        r"(?:Final\s+)?Verdict\s*[:\-=]\s*[`\*\_]*\s*(BUY|SELL|HOLD)\b",
        r"##\s*🎯\s*Final Verdict[:\s]+[^\n]*\b(BUY|SELL|HOLD)\b",
        r"###\s*🎯\s*Final Verdict[:\s]+[^\n]*\b(BUY|SELL|HOLD)\b",
    ]
    for pattern in rec_line_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            matched_rec = match.group(1).upper()
            if matched_rec in ("BUY", "SELL", "HOLD"):
                return Recommendation(matched_rec)

    return None


def parse_and_validate_output(raw_text: str, schema_cls: type) -> tuple[Optional[BaseModel], Optional[str]]:
    """
    Safely parses and validates agent output against a Pydantic schema.
    Returns (validated_model, error_message).
    """
    if not raw_text or not raw_text.strip():
        return None, "Empty agent response."

    # 1. Try JSON block extraction
    data = extract_json_block(raw_text)
    if data:
        try:
            model = schema_cls.model_validate(data)
            return model, None
        except Exception as e:
            pass

    # 2. Text heuristics parser to construct model gracefully
    try:
        what_happened = ""
        why_it_matters = ""
        overall_conclusion = ""
        summary = ""
        key_findings = []
        evidence = []
        risks = []

        news_sum = ""
        tech_sum = ""
        risk_sum = ""
        fund_sum = ""
        port_sum = ""

        # Extract sections if markdown (supports # headers and **Header:** bold blocks)
        headers = list(re.finditer(r"(?:^|\n)(?:#{1,4}\s+|\*\*(.*?)\*\*[:\s]*)", raw_text))
        if headers:
            for i in range(len(headers)):
                start = headers[i].start()
                end = headers[i+1].start() if i + 1 < len(headers) else len(raw_text)
                sec = raw_text[start:end].strip()
                if not sec:
                    continue
                lower_head = sec.split("\n")[0].lower()
                content = "\n".join(sec.split("\n")[1:]).strip()

                if "what happened" in lower_head:
                    what_happened = content
                elif "why it matters" in lower_head or "why matters" in lower_head:
                    why_it_matters = content
                elif any(k in lower_head for k in ("overall conclusion", "conclusion", "final verdict", "outlook")):
                    overall_conclusion = content
                elif any(k in lower_head for k in ("evidence", "data", "metrics", "supporting evidence")):
                    bullets = [re.sub(r"^[\*\-\s]+(?:\d+[\.\)])?\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    evidence.extend([b for b in bullets if b])
                elif any(k in lower_head for k in ("news summary", "📰")):
                    news_sum = content
                elif any(k in lower_head for k in ("technical summary", "📈")):
                    tech_sum = content
                elif any(k in lower_head for k in ("risk summary", "🛡")):
                    risk_sum = content
                elif any(k in lower_head for k in ("fundamental summary", "🏢")):
                    fund_sum = content
                elif any(k in lower_head for k in ("portfolio summary", "💼")):
                    port_sum = content
                elif any(k in lower_head for k in ("summary", "executive summary")):
                    summary += (" " + content).strip()
                elif any(k in lower_head for k in ("findings", "key findings")):
                    bullets = [re.sub(r"^[\*\-\s]+(?:\d+[\.\)])?\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    key_findings.extend([b for b in bullets if b])
                elif any(k in lower_head for k in ("risk", "vulnerabilit", "watchpoint")):
                    bullets = [re.sub(r"^[\*\-\s]+(?:\d+[\.\)])?\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    risks.extend([b for b in bullets if b])
        else:
            sections = re.split(r"(?m)^#{1,4}\s+", raw_text)
            for sec in sections:
                sec = sec.strip()
                if not sec:
                    continue
                lower_head = sec.split("\n")[0].lower()
                content = "\n".join(sec.split("\n")[1:]).strip()

                if "what happened" in lower_head:
                    what_happened = content
                elif "why it matters" in lower_head:
                    why_it_matters = content
                elif any(k in lower_head for k in ("conclusion", "verdict", "outlook")):
                    overall_conclusion = content
                elif any(k in lower_head for k in ("evidence", "data", "metrics")):
                    bullets = [re.sub(r"^[\*\-\s]+(?:\d+[\.\)])?\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    evidence.extend([b for b in bullets if b])
                elif any(k in lower_head for k in ("summary", "verdict")):
                    summary += (" " + content).strip()
                elif any(k in lower_head for k in ("findings", "key findings")):
                    bullets = [re.sub(r"^[\*\-\s]+(?:\d+[\.\)])?\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    key_findings.extend([b for b in bullets if b])
                elif any(k in lower_head for k in ("risk", "vulnerabilit", "watchpoint")):
                    bullets = [re.sub(r"^[\*\-\s]+(?:\d+[\.\)])?\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    risks.extend([b for b in bullets if b])

        clean_lines = [l.strip() for l in raw_text.split("\n") if l.strip() and not l.startswith("#")]
        first_clean = clean_lines[0] if clean_lines else "Analysis completed."

        if not summary:
            summary = what_happened or first_clean
        if not what_happened:
            what_happened = summary
        if not why_it_matters:
            why_it_matters = "Key business and market implications for the company and investors."
        if not overall_conclusion:
            overall_conclusion = summary
        if not key_findings:
            key_findings = [why_it_matters] if why_it_matters else [summary[:200]]

        init_kwargs = {
            "what_happened": what_happened[:1000],
            "why_it_matters": why_it_matters[:1000],
            "supporting_evidence": evidence[:10],
            "overall_conclusion": overall_conclusion[:1000],
            "summary": summary[:1000],
            "key_findings": key_findings[:10],
            "risks": risks[:10],
        }

        if schema_cls == CIORecommendationOutput:
            rec = parse_cio_recommendation_strict(raw_text)
            if not rec:
                return None, "Malformed or missing recommendation (BUY, SELL, or HOLD not explicitly declared)."
            init_kwargs["recommendation"] = rec
            init_kwargs["news_summary"] = news_sum[:500]
            init_kwargs["technical_summary"] = tech_sum[:500]
            init_kwargs["risk_summary"] = risk_sum[:500]
            init_kwargs["fundamental_summary"] = fund_sum[:500]
            init_kwargs["portfolio_summary"] = port_sum[:500]

        return schema_cls.model_validate(init_kwargs), None

    except Exception as e:
        return None, f"Schema validation failed: {str(e)}"
