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
    summary: str = Field(..., description="High-level executive summary of the analysis")
    key_findings: List[str] = Field(default_factory=list, description="List of key findings identified")
    supporting_evidence: List[str] = Field(default_factory=list, description="Data points and metrics supporting findings")
    risks: List[str] = Field(default_factory=list, description="Key risks identified during analysis")

    def to_markdown(self) -> str:
        """Fallback markdown generator."""
        lines = [
            f"### Summary\n{self.summary}\n",
            "### Key Findings",
            "\n".join(f"- {f}" for f in self.key_findings) if self.key_findings else "- None noted.",
            "\n### Supporting Evidence",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- None noted.",
            "\n### Risks",
            "\n".join(f"- {r}" for r in self.risks) if self.risks else "- None noted.",
        ]
        return "\n".join(lines)


class NewsAnalysisOutput(BaseAgentOutput):
    sentiment: str = Field(default="NEUTRAL", description="Overall news sentiment: BULLISH, BEARISH, or NEUTRAL")
    relevant_headlines_count: int = Field(default=0, description="Number of news items analyzed")
    data_freshness: str = Field(default="Recent", description="Freshness of the analyzed news")

    def to_markdown(self, ticker: str = "") -> str:
        heading = f"## News Report for {ticker}" if ticker else "## News Report"
        return (
            f"{heading}\n\n"
            f"**Sentiment**: `{self.sentiment.upper()}` ({self.relevant_headlines_count} sources analyzed, {self.data_freshness})\n\n"
            f"**What happened?**\n{self.summary}\n\n"
            f"**Key Findings:**\n" + ("\n".join(f"- {f}" for f in self.key_findings) if self.key_findings else "- No significant developments.") + "\n\n"
            f"**Supporting Evidence:**\n" + ("\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- None available.") + "\n\n"
            f"**Risks & Watchpoints:**\n" + ("\n".join(f"- {r}" for r in self.risks) if self.risks else "- Standard market risk.")
        )


class TechnicalAnalysisOutput(BaseAgentOutput):
    trend_bias: str = Field(default="NEUTRAL", description="BULLISH, BEARISH, or NEUTRAL")
    rsi_14: Optional[float] = Field(default=None, description="RSI indicator value")
    macd_signal: Optional[str] = Field(default=None, description="MACD interpretation")
    support_level: Optional[float] = Field(default=None, description="Key support price")
    resistance_level: Optional[float] = Field(default=None, description="Key resistance price")
    indicators_summary: Dict[str, Any] = Field(default_factory=dict, description="Raw or parsed indicator values")

    def to_markdown(self, ticker: str = "") -> str:
        heading = f"## Technical Report for {ticker}" if ticker else "## Technical Report"
        rsi_str = f" | RSI(14): {self.rsi_14:.1f}" if self.rsi_14 is not None else ""
        macd_str = f" | MACD: {self.macd_signal}" if self.macd_signal else ""
        return (
            f"{heading}\n\n"
            f"**Technical Bias**: `{self.trend_bias.upper()}`{rsi_str}{macd_str}\n\n"
            f"**What happened?**\n{self.summary}\n\n"
            f"**Key Findings:**\n" + ("\n".join(f"- {f}" for f in self.key_findings) if self.key_findings else "- Price consolidating.") + "\n\n"
            f"**Supporting Evidence:**\n" + ("\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Indicator data applied.") + "\n\n"
            f"**Risks & Technical Vulnerabilities:**\n" + ("\n".join(f"- {r}" for r in self.risks) if self.risks else "- Standard market volatility.")
        )


class RiskAnalysisOutput(BaseAgentOutput):
    risk_level: str = Field(default="MODERATE", description="LOW, MODERATE, HIGH, or EXTREME")
    annualized_volatility: Optional[float] = Field(default=None, description="Annualized volatility percentage")
    var_95: Optional[float] = Field(default=None, description="Value at Risk (95% confidence)")
    max_drawdown: Optional[float] = Field(default=None, description="Maximum historical drawdown percentage")

    def to_markdown(self, ticker: str = "") -> str:
        heading = f"## Risk Report for {ticker}" if ticker else "## Risk Report"
        vol_str = f" | Ann. Volatility: {self.annualized_volatility:.1f}%" if self.annualized_volatility is not None else ""
        var_str = f" | VaR (95%): {self.var_95:.1f}%" if self.var_95 is not None else ""
        return (
            f"{heading}\n\n"
            f"**Risk Level**: `{self.risk_level.upper()}`{vol_str}{var_str}\n\n"
            f"**What happened?**\n{self.summary}\n\n"
            f"**Key Risk Findings:**\n" + ("\n".join(f"- {f}" for f in self.key_findings) if self.key_findings else "- Normal market risk profile.") + "\n\n"
            f"**Supporting Evidence:**\n" + ("\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Quantitative risk metrics.") + "\n\n"
            f"**Stress Scenarios & Vulnerabilities:**\n" + ("\n".join(f"- {r}" for r in self.risks) if self.risks else "- None specified.")
        )


class FundamentalAnalysisOutput(BaseAgentOutput):
    valuation_assessment: str = Field(default="FAIR", description="UNDERVALUED, FAIR, or OVERVALUED")
    pe_ratio: Optional[float] = Field(default=None, description="Trailing P/E ratio")
    revenue_growth_yoy: Optional[float] = Field(default=None, description="YoY revenue growth percentage")
    profit_margins: Optional[str] = Field(default=None, description="Margin assessment")

    def to_markdown(self, ticker: str = "") -> str:
        heading = f"## Fundamental Report for {ticker}" if ticker else "## Fundamental Report"
        val_str = f"**Valuation Assessment**: `{self.valuation_assessment.upper()}`"
        pe_str = f" | P/E: {self.pe_ratio:.1f}" if self.pe_ratio is not None else ""
        return (
            f"{heading}\n\n"
            f"{val_str}{pe_str}\n\n"
            f"**What happened?**\n{self.summary}\n\n"
            f"**Key Findings:**\n" + ("\n".join(f"- {f}" for f in self.key_findings) if self.key_findings else "- Financials consistent with expectations.") + "\n\n"
            f"**Supporting Evidence:**\n" + ("\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Corporate disclosures & filings.") + "\n\n"
            f"**Fundamental Risks:**\n" + ("\n".join(f"- {r}" for r in self.risks) if self.risks else "- Competitive and macroeconomic headwinds.")
        )


class PortfolioAnalysisOutput(BaseAgentOutput):
    allocation_status: str = Field(default="BALANCED", description="OVERWEIGHT, UNDERWEIGHT, or BALANCED")
    diversification_score: Optional[float] = Field(default=None, description="Diversification score out of 100")
    rebalancing_action: Optional[str] = Field(default=None, description="Suggested rebalance action")

    def to_markdown(self, portfolio_id: str = "") -> str:
        p_label = f" for {portfolio_id}" if portfolio_id else ""
        return (
            f"## Portfolio Report{p_label}\n\n"
            f"**Allocation Status**: `{self.allocation_status.upper()}`\n\n"
            f"**What happened?**\n{self.summary}\n\n"
            f"**Key Findings:**\n" + ("\n".join(f"- {f}" for f in self.key_findings) if self.key_findings else "- Holdings align with risk profile.") + "\n\n"
            f"**Supporting Evidence:**\n" + ("\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Current portfolio weights.") + "\n\n"
            f"**Portfolio Concentration & Balance Risks:**\n" + ("\n".join(f"- {r}" for r in self.risks) if self.risks else "- No severe concentration detected.")
        )


class CIORecommendationOutput(BaseAgentOutput):
    recommendation: Recommendation = Field(..., description="Mandatory verdict: BUY, SELL, or HOLD")
    time_horizon: str = Field(default="Medium-term (3-12 months)", description="Investment horizon")
    conflicting_signals: List[str] = Field(default_factory=list, description="Contradictions between agents identified")
    limitations_and_missing_data: List[str] = Field(default_factory=list, description="Missing metrics or limits to analysis")
    confidence_score: float = Field(default=0.0, description="Evidence-calibrated confidence score between 0 and 100")

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
            f"### 🎯 Final Verdict: {rec_color_emoji} **{rec_badge}** (Horizon: {self.time_horizon})",
            f"**Analysis Confidence**: `{self.confidence_score:.1f}%`",
            "",
            f"## 📋 Executive Summary\n{self.summary}\n",
            "## 🔍 Key Findings",
            "\n".join(f"- {f}" for f in self.key_findings) if self.key_findings else "- Analysis completed.",
            "",
            "## 📊 Supporting Evidence",
            "\n".join(f"- {e}" for e in self.supporting_evidence) if self.supporting_evidence else "- Multi-agent research findings.",
            "",
        ]

        if self.conflicting_signals:
            lines.extend([
                "## ⚠️ Conflicting Findings & Divergences",
                "\n".join(f"- {c}" for c in self.conflicting_signals),
                ""
            ])

        if self.limitations_and_missing_data:
            lines.extend([
                "## ℹ️ Limitations & Missing Data",
                "\n".join(f"- {m}" for m in self.limitations_and_missing_data),
                ""
            ])

        lines.extend([
            "## 🛡️ Downside Risks",
            "\n".join(f"- {r}" for r in self.risks) if self.risks else "- Market-wide risk factors apply.",
            "",
            "---",
            "## 🎯 Overall Investment Outlook",
            self.summary
        ])

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
        summary = ""
        key_findings = []
        evidence = []
        risks = []

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

                if any(k in lower_head for k in ("what happened", "summary", "conclusion", "verdict")):
                    summary += (" " + content).strip()
                elif any(k in lower_head for k in ("findings", "why it matters")):
                    bullets = [re.sub(r"^[\*\-\d\.]+\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    key_findings.extend([b for b in bullets if b])
                elif any(k in lower_head for k in ("evidence", "data", "metrics")):
                    bullets = [re.sub(r"^[\*\-\d\.]+\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    evidence.extend([b for b in bullets if b])
                elif any(k in lower_head for k in ("risk", "vulnerabilit", "watchpoint")):
                    bullets = [re.sub(r"^[\*\-\d\.]+\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    risks.extend([b for b in bullets if b])
        else:
            sections = re.split(r"(?m)^#{1,4}\s+", raw_text)
            for sec in sections:
                sec = sec.strip()
                if not sec:
                    continue
                lower_head = sec.split("\n")[0].lower()
                content = "\n".join(sec.split("\n")[1:]).strip()

                if any(k in lower_head for k in ("what happened", "summary", "conclusion", "verdict")):
                    summary += (" " + content).strip()
                elif any(k in lower_head for k in ("findings", "why it matters")):
                    bullets = [re.sub(r"^[\*\-\d\.]+\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    key_findings.extend([b for b in bullets if b])
                elif any(k in lower_head for k in ("evidence", "data", "metrics")):
                    bullets = [re.sub(r"^[\*\-\d\.]+\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    evidence.extend([b for b in bullets if b])
                elif any(k in lower_head for k in ("risk", "vulnerabilit", "watchpoint")):
                    bullets = [re.sub(r"^[\*\-\d\.]+\s*", "", b).strip() for b in content.split("\n") if b.strip()]
                    risks.extend([b for b in bullets if b])

        if not summary:
            # Fall back to first couple sentences
            clean_lines = [l.strip() for l in raw_text.split("\n") if l.strip() and not l.startswith("#")]
            summary = clean_lines[0] if clean_lines else "Analysis completed."

        if not key_findings:
            key_findings = [summary[:200]]

        init_kwargs = {
            "summary": summary[:1000],
            "key_findings": key_findings[:5],
            "supporting_evidence": evidence[:5],
            "risks": risks[:5],
        }

        if schema_cls == CIORecommendationOutput:
            rec = parse_cio_recommendation_strict(raw_text)
            if not rec:
                return None, "Malformed or missing recommendation (BUY, SELL, or HOLD not explicitly declared)."
            init_kwargs["recommendation"] = rec

        return schema_cls.model_validate(init_kwargs), None

    except Exception as e:
        return None, f"Schema validation failed: {str(e)}"
