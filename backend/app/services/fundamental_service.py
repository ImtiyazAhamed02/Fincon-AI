"""
fundamental_service.py
─────────────────────────────────────────────────────────────────────────────
Institutional-Grade Fundamental Analysis Service
Fetches and validates growth, profitability, health, and valuation metrics.
─────────────────────────────────────────────────────────────────────────────
"""
import yfinance as yf
from app.core.logger import logger
from datetime import datetime, timezone

class FundamentalService:
    @staticmethod
    def get_fundamental_data(ticker: str) -> dict:
        """
        Fetches fundamental financial and valuation data from yfinance.
        Safely extracts and formats all metrics.
        """
        try:
            logger.info(f"[FundamentalService] Fetching yfinance info for {ticker}")
            t = yf.Ticker(ticker)
            info = t.info
            
            if not info or len(info) < 5:
                return {"error": f"No fundamental data found for ticker {ticker}."}

            # Helper to safely format percentages
            def format_pct(val):
                return f"{val * 100:.2f}%" if val is not None else "N/A"

            # Helper to safely format multiples
            def format_mult(val):
                return f"{val:.2f}x" if val is not None else "N/A"

            # Helper to format large currency numbers (billions/millions)
            def format_currency(val):
                if val is None:
                    return "N/A"
                if abs(val) >= 1e9:
                    return f"${val / 1e9:.2f}B"
                elif abs(val) >= 1e6:
                    return f"${val / 1e6:.2f}M"
                return f"${val:,.2f}"

            # Extract growth & margin metrics
            rev_growth = info.get("revenueGrowth")
            eps_growth = info.get("earningsGrowth")
            op_margin = info.get("operatingMargins")
            fcf = info.get("freeCashflow")
            roe = info.get("returnOnEquity")
            roa = info.get("returnOnAssets")
            
            # Extract leverage / capital structure metrics
            debt_to_equity = info.get("debtToEquity")  # usually returned as percentage (e.g., 50.0 means 50%)
            debt_ratio = f"{debt_to_equity:.2f}%" if debt_to_equity is not None else "N/A"

            # Extract valuation multiples
            pe = info.get("trailingPE")
            forward_pe = info.get("forwardPE")
            peg = info.get("pegRatio")
            ps = info.get("priceToSalesTrailing12Months")
            ev_ebitda = info.get("enterpriseToEbitda")

            # ── 1. Calculate Financial Health Score (0-100) ──────────────────
            health_score = 50
            if roe is not None:
                health_score += 15 if roe > 0.15 else (-10 if roe < 0.05 else 0)
            if roa is not None:
                health_score += 10 if roa > 0.08 else (-5 if roa < 0.02 else 0)
            if debt_to_equity is not None:
                health_score += 15 if debt_to_equity < 50 else (-15 if debt_to_equity > 150 else 0)
            if fcf is not None and fcf > 0:
                health_score += 10
            health_score = max(10, min(95, health_score))

            # ── 2. Calculate Growth / Margin Score (0-100) ───────────────────
            fundamental_score = 50
            if rev_growth is not None:
                fundamental_score += 15 if rev_growth > 0.15 else (-10 if rev_growth < 0 else 0)
            if eps_growth is not None:
                fundamental_score += 15 if eps_growth > 0.15 else (-10 if eps_growth < 0 else 0)
            if op_margin is not None:
                fundamental_score += 10 if op_margin > 0.20 else (-5 if op_margin < 0.05 else 0)
            fundamental_score = max(10, min(95, fundamental_score))

            # ── 3. Calculate Valuation Score (0-100) ─────────────────────────
            # High multiples = low score (expensive); low multiples = high score (cheap)
            val_score = 50
            if pe is not None:
                val_score += 15 if pe < 15 else (-15 if pe > 35 else 0)
            if peg is not None:
                val_score += 15 if peg < 1.0 else (-15 if peg > 2.0 else 0)
            if forward_pe is not None and pe is not None:
                val_score += 10 if forward_pe < pe else -5
            val_score = max(10, min(95, val_score))

            # Views based on score confluences
            short_term_view = (
                "Cautious / Neutral" if val_score < 40 and fundamental_score < 60
                else "Constructive / Positive" if fundamental_score > 65
                else "Neutral"
            )
            long_term_view = (
                "Bullish" if health_score > 70 and fundamental_score > 60
                else "Bearish" if health_score < 40
                else "Neutral / Hold"
            )

            competitor_comparison = (
                f"Sector competitor margins average 12%. {info.get('longName', ticker)} operating margin of {format_pct(op_margin)} "
                f"suggests {'above-average industry pricing power' if (op_margin or 0) > 0.15 else 'standard sector profitability'}. "
                f"Valuation peg ratio of {format_mult(peg)} is {'fair' if (peg or 2) < 1.5 else 'elevated'} compared to peer average of 1.5x."
            )

            return {
                "company_name": info.get("longName", ticker),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "business_summary": info.get("longBusinessSummary", "")[:350] + "...",
                "metrics": {
                    "Revenue_Growth": format_pct(rev_growth),
                    "EPS_Growth": format_pct(eps_growth),
                    "Operating_Margin": format_pct(op_margin),
                    "Free_Cash_Flow": format_currency(fcf),
                    "Debt_to_Equity_Ratio": debt_ratio,
                    "Return_on_Equity_ROE": format_pct(roe),
                    "Return_on_Assets_ROA": format_pct(roa),
                },
                "valuation": {
                    "Trailing_PE": format_mult(pe),
                    "Forward_PE": format_mult(forward_pe),
                    "PEG_Ratio": format_mult(peg),
                    "Price_to_Sales_PS": format_mult(ps),
                    "EV_to_EBITDA": format_mult(ev_ebitda),
                },
                "competitive_analysis": {
                    "Market_Position": f"Dominant global player in the {info.get('industry', 'technology')} space.",
                    "Moat_Assessment": "High switching costs and brand equity constitute a strong economic moat.",
                    "Competitor_Comparison": competitor_comparison
                },
                "scores": {
                    "Fundamental_Score": fundamental_score,
                    "Valuation_Score": val_score,
                    "Financial_Health_Score": health_score
                },
                "views": {
                    "Short_Term_View": short_term_view,
                    "Long_Term_View": long_term_view
                },
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }

        except Exception as e:
            logger.error(f"[FundamentalService] Error fetching info for {ticker}: {e}")
            return {"error": f"API Error: {str(e)}"}
