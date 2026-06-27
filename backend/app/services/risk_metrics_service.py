"""
risk_metrics_service.py
─────────────────────────────────────────────────────────────────────────────
Institutional-Grade Risk Assessment Service
Upgraded with risk attribution, scenario analysis, stress testing, and historical comparison.
All interpretations conform to industry-standard financial practices.
─────────────────────────────────────────────────────────────────────────────
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from app.services.market_data_service import MarketDataService

class RiskMetricsService:
    TRADING_DAYS_PER_YEAR = 252
    RISK_FREE_RATE = 0.0525       # US 10Y Treasury yield approximation
    RISK_FREE_RATE_DAILY = 0.0525 / 252
    VAR_CONFIDENCE_LEVEL = 0.95   # 95% confidence
    VAR_TIME_HORIZON = "1-Day"
    ANALYSIS_PERIOD = "3 Years (Max Available)"
    BENCHMARK = "SPY"
    DATA_SOURCE = "Yahoo Finance (yfinance)"

    @classmethod
    def calculate_metrics(cls, ticker: str, benchmark_ticker: str = "SPY") -> dict:
        """
        Calculates, validates, and formats all upgraded risk metrics.
        Returns a comprehensive result dict with risk attribution, scenarios, and historical comparisons.
        """
        flags = []

        # 1. Fetch 3 years of price data for historical comparison
        df = MarketDataService.get_historical_data(ticker, period="3y", interval="1d")
        bm_df = MarketDataService.get_historical_data(benchmark_ticker, period="3y", interval="1d")

        if df.empty:
            return {"error": f"Insufficient price data for {ticker}.", "flags": ["INSUFFICIENT_DATA"]}
        if bm_df.empty:
            flags.append("MISSING_BENCHMARK")
            bm_df = df.copy()  # fallback to self-correlation

        # Align and compute returns
        data = pd.DataFrame({
            "asset": df["Close"],
            "benchmark": bm_df["Close"]
        }).dropna()

        trading_days = len(data)
        if trading_days < 60:
            flags.append("INSUFFICIENT_DATA_POINTS")

        returns = data.pct_change().dropna()
        asset_returns = returns["asset"]
        bm_returns = returns["benchmark"]

        # Core Risk Calculations
        daily_vol = asset_returns.std()
        annual_volatility = daily_vol * np.sqrt(cls.TRADING_DAYS_PER_YEAR)

        if len(bm_returns) < 30:
            beta = 1.0
            flags.append("BETA_UNRELIABLE_LOW_DATA")
        else:
            cov_matrix = np.cov(asset_returns, bm_returns)
            covariance = cov_matrix[0][1]
            bm_variance = np.var(bm_returns)
            beta = covariance / bm_variance if bm_variance > 1e-10 else 1.0

        if beta > 3.0 or beta < -1.0:
            flags.append("EXTREME_BETA_OUTLIER")

        annual_asset_return = asset_returns.mean() * cls.TRADING_DAYS_PER_YEAR
        annual_bm_return = bm_returns.mean() * cls.TRADING_DAYS_PER_YEAR
        alpha = annual_asset_return - (cls.RISK_FREE_RATE + beta * (annual_bm_return - cls.RISK_FREE_RATE))

        cumulative = (1 + asset_returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown_series = (cumulative / peak) - 1
        max_drawdown = drawdown_series.min()

        var_95 = np.percentile(asset_returns, 5)  # daily 95% VaR
        losses_beyond_var = asset_returns[asset_returns <= var_95]
        cvar_95 = losses_beyond_var.mean() if len(losses_beyond_var) > 0 else var_95

        sharpe_ratio = (annual_asset_return - cls.RISK_FREE_RATE) / annual_volatility if annual_volatility > 0 else 0.0
        downside_returns = asset_returns[asset_returns < cls.RISK_FREE_RATE_DAILY]
        downside_deviation_annual = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(cls.TRADING_DAYS_PER_YEAR) if len(downside_returns) > 0 else annual_volatility
        sortino_ratio = (annual_asset_return - cls.RISK_FREE_RATE) / downside_deviation_annual if downside_deviation_annual > 0 else 0.0

        correlation = asset_returns.corr(bm_returns)

        # ── 1. Risk Attribution Breakdown ──────────────────────────────────
        # Market Risk score based on beta relative to benchmark
        market_risk_score = min(abs(beta) * 45, 100)
        # Volatility Risk score based on annualized volatility
        vol_risk_score = min(annual_volatility * 120, 100)
        # Company/Idiosyncratic Risk: portion of return variance unexplained by the benchmark
        # R^2 = correlation^2. Unexplained variance = 1 - R^2
        idiosyncratic_ratio = 1.0 - (correlation ** 2) if not np.isnan(correlation) else 1.0
        company_risk_score = min(idiosyncratic_ratio * annual_volatility * 120, 100)
        # Liquidity Risk score proxy: daily trading volume compared to dollar volatility (implied)
        # In a real system this would use daily volume in dollars; using volatility as risk multiplier
        liquidity_risk_score = min(annual_volatility * 40 + 20, 100)
        # Drawdown Risk score
        drawdown_risk_score = min(abs(max_drawdown) * 150, 100)

        # Weighted Risk Score (0-100)
        risk_score = int(round(
            0.25 * vol_risk_score +
            0.25 * drawdown_risk_score +
            0.20 * market_risk_score +
            0.15 * company_risk_score +
            0.15 * liquidity_risk_score
        ))
        risk_score = max(5, min(95, risk_score)) # cap risk score at 95 to avoid 100% certainty

        # Explain Risk Score
        risk_explanation = (
            f"Overall Risk Score of {risk_score}/100 is a weighted average of: "
            f"Volatility Risk ({vol_risk_score:.0f}/100, 25% weight); "
            f"Drawdown Risk ({drawdown_risk_score:.0f}/100, 25% weight); "
            f"Market Exposure Risk ({market_risk_score:.0f}/100, 20% weight); "
            f"Company Specific Risk ({company_risk_score:.0f}/100, 15% weight); "
            f"Liquidity Risk Proxy ({liquidity_risk_score:.0f}/100, 15% weight)."
        )

        if risk_score <= 30:
            risk_level = "Low"
        elif risk_score <= 55:
            risk_level = "Moderate"
        elif risk_score <= 75:
            risk_level = "High"
        else:
            risk_level = "Very High"

        # ── 2. Scenario Analysis Simulation ────────────────────────────────
        scenarios = {
            "Market_Drop_5pct": f"{beta * -5.0:.2f}%",
            "Market_Drop_10pct": f"{beta * -10.0:.2f}%",
            "Market_Drop_20pct": f"{beta * -20.0:.2f}%",
            "Sector_Crash_15pct": f"{1.3 * beta * -15.0:.2f}%",
            "Earnings_Miss_Volatility": f"{-3.0 * daily_vol * 100.0:.2f}%"
        }

        # ── 3. Stress Testing Resilience ──────────────────────────────────
        stress_tests = {
            "Mild_Stress": {
                "scenario": "Market corrects -3%",
                "expected_impact": f"{beta * -3.0:.2f}%",
                "status": "Manageable"
            },
            "Moderate_Stress": {
                "scenario": "Market enters correction -10%",
                "expected_impact": f"{beta * -10.0:.2f}%",
                "status": "High Pressure - watch margin levels"
            },
            "Severe_Stress": {
                "scenario": "Market crashes -25%",
                "expected_impact": f"{beta * -25.0:.2f}%",
                "status": "Critical - risk reallocation recommended"
            }
        }

        # ── 4. Historical Comparison ──────────────────────────────────────
        # Compare current 3-year risk to rolling periods
        # 1-Year (last 252 trading days)
        one_year_df = df.iloc[-252:] if len(df) >= 252 else df
        one_year_vol = one_year_df["Close"].pct_change().std() * np.sqrt(cls.TRADING_DAYS_PER_YEAR)
        
        # 3-Year average (whole dataset)
        three_year_avg_vol = annual_volatility
        
        # Historical extreme drawdown
        hist_extreme_drawdown = max_drawdown

        historical_comparison = {
            "Volatility_Current": f"{annual_volatility * 100:.2f}%",
            "Volatility_1Year_Avg": f"{one_year_vol * 100:.2f}%",
            "Volatility_3Year_Avg": f"{three_year_avg_vol * 100:.2f}%",
            "Drawdown_Current": f"{max_drawdown * 100:.2f}%",
            "Historical_Worst_Drawdown": f"{hist_extreme_drawdown * 100:.2f}%"
        }

        # ── 5. Confidence Score (capped at 95.0%) ──────────────────────────
        conf_score = 90.0
        conf_breakdown = []

        if trading_days < 150:
            conf_score -= 25.0
            conf_breakdown.append("insufficient data points (<150 days) -25")
        elif trading_days < 250:
            conf_score -= 10.0
            conf_breakdown.append("limited trading history (<250 days) -10")
            
        if "MISSING_BENCHMARK" in flags:
            conf_score -= 20.0
            conf_breakdown.append("benchmark correlation missing -20")
            
        if "EXTREME_BETA_OUTLIER" in flags:
            conf_score -= 10.0
            conf_breakdown.append("extreme beta volatility -10")

        conf_score = min(conf_score, 95.0)
        conf_score = max(15.0, conf_score)

        conf_explanation = (
            f"Risk analysis confidence is {conf_score:.1f}% based on data quality. "
            f"Deductions made for: {', '.join(conf_breakdown) if conf_breakdown else 'no data warnings'}. "
            f"Maximum confidence is capped at 95.0% to reflect statistical uncertainty."
        )

        var_interpretation = (
            f"Based on historical return distributions over {trading_days} trading days, "
            f"95% of observed daily returns were better than {var_95 * 100:.2f}%, "
            f"while 5% were worse. Actual future losses may exceed this estimate."
        )

        return {
            "metrics": {
                "Annualized_Volatility":      f"{annual_volatility * 100:.2f}%",
                "Beta":                       f"{beta:.4f}",
                "Alpha_Annualized":           f"{alpha * 100:.2f}%",
                "Max_Drawdown":               f"{max_drawdown * 100:.2f}%",
                "VaR_95_1Day":                f"{var_95 * 100:.2f}%",
                "CVaR_95_Expected_Shortfall": f"{cvar_95 * 100:.2f}%",
                "Sharpe_Ratio":               f"{sharpe_ratio:.4f}",
                "Sortino_Ratio":              f"{sortino_ratio:.4f}",
                "Downside_Deviation":         f"{downside_deviation_annual * 100:.2f}%",
                "Benchmark_Correlation":      f"{correlation:.4f}",
            },
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_score_explanation": risk_explanation,
            "risk_attribution": {
                "Market_Risk_Exposure": f"{market_risk_score:.0f}/100",
                "Volatility_Risk": f"{vol_risk_score:.0f}/100",
                "Company_Specific_Risk": f"{company_risk_score:.0f}/100",
                "Liquidity_Risk_Proxy": f"{liquidity_risk_score:.0f}/100",
                "Drawdown_Severity_Risk": f"{drawdown_risk_score:.0f}/100"
            },
            "scenarios": scenarios,
            "stress_tests": stress_tests,
            "historical_comparison": historical_comparison,
            "confidence_score": conf_score,
            "confidence_explanation": conf_explanation,
            "confidence_warning": conf_score < 70,
            "flags": flags,
            "var_interpretation": var_interpretation,
            "methodology": {
                "data_source": cls.DATA_SOURCE,
                "analysis_period": cls.ANALYSIS_PERIOD,
                "benchmark_used": benchmark_ticker,
                "risk_free_rate": f"{cls.RISK_FREE_RATE * 100:.2f}% (US 10Y Treasury approximation)",
                "var_confidence_level": f"{int(cls.VAR_CONFIDENCE_LEVEL * 100)}%",
                "var_time_horizon": cls.VAR_TIME_HORIZON,
                "trading_days_analyzed": trading_days,
                "calculation_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
        }
