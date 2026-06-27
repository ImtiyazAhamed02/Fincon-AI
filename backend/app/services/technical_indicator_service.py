"""
technical_indicator_service.py
─────────────────────────────────────────────────────────────────────────────
Institutional-Grade Technical Analysis Service
Calculates multi-timeframe indicators, signal conflicts, risk signals, and trade quality scores.
─────────────────────────────────────────────────────────────────────────────
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from app.core.logger import logger

class TechnicalIndicatorService:

    @staticmethod
    def calculate_sma(series: pd.Series, window: int) -> pd.Series:
        return series.rolling(window=window).mean()

    @staticmethod
    def calculate_ema(series: pd.Series, window: int) -> pd.Series:
        return series.ewm(span=window, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        ema_fast = TechnicalIndicatorService.calculate_ema(series, fast)
        ema_slow = TechnicalIndicatorService.calculate_ema(series, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicatorService.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        return pd.DataFrame({"MACD": macd_line, "Signal": signal_line, "Histogram": histogram})

    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        sma = TechnicalIndicatorService.calculate_sma(series, window)
        rolling_std = series.rolling(window=window).std()
        return pd.DataFrame({
            "Upper": sma + rolling_std * num_std,
            "Middle": sma,
            "Lower": sma - rolling_std * num_std,
        })

    @staticmethod
    def calculate_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=window).mean()

    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> dict:
        close = df["Close"]
        high = df["High"]
        low = df["Low"]

        recent_high = high.rolling(window=window).max().iloc[-1]
        recent_low = low.rolling(window=window).min().iloc[-1]
        pivot = (high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3

        r1 = round((2 * pivot) - recent_low, 2)
        s1 = round((2 * pivot) - recent_high, 2)
        r2 = round(pivot + (recent_high - recent_low), 2)
        s2 = round(pivot - (recent_high - recent_low), 2)

        return {
            "Pivot_Point":    round(pivot, 2),
            "Resistance_R1":  r1,
            "Resistance_R2":  r2,
            "Support_S1":     s1,
            "Support_S2":     s2,
            "52W_High":       round(high.rolling(min(252, len(df))).max().iloc[-1], 2),
            "52W_Low":        round(low.rolling(min(252, len(df))).min().iloc[-1], 2),
        }

    @staticmethod
    def analyze_volume(df: pd.DataFrame, window: int = 20) -> dict:
        if "Volume" not in df.columns:
            return {"Volume_Trend": "Data unavailable", "Volume_Signal": "NEUTRAL", "Volume_Ratio_to_Avg": 1.0, "Current_Volume": 0, "Avg_Volume_20D": 0}

        vol = df["Volume"]
        avg_vol = vol.rolling(window=window).mean()
        current_vol = vol.iloc[-1]
        avg_vol_val = avg_vol.iloc[-1]
        ratio = current_vol / avg_vol_val if avg_vol_val > 0 else 1.0

        if ratio > 1.5:
            trend = "High Volume — strong participation, signals carry more weight."
            signal = "STRONG"
        elif ratio > 1.0:
            trend = "Above-average volume — moderate participation."
            signal = "ABOVE_AVERAGE"
        elif ratio > 0.7:
            trend = "Below-average volume — signals carry less conviction."
            signal = "BELOW_AVERAGE"
        else:
            trend = "Very low volume — signals are unreliable; exercise caution."
            signal = "WEAK"

        return {
            "Current_Volume":        int(current_vol),
            "Avg_Volume_20D":        int(avg_vol_val),
            "Volume_Ratio_to_Avg":   round(ratio, 2),
            "Volume_Trend":          trend,
            "Volume_Signal":         signal,
        }

    @staticmethod
    def classify_trend_score(rsi: float, macd_hist: float, price_vs_sma20: float, price_vs_sma50: float) -> tuple:
        """Classifies trend and returns trend label, description, and score."""
        score = 50  # base
        
        # RSI contribution
        if rsi > 60:
            score += min(15, (rsi - 60) * 0.5)
        elif rsi < 40:
            score -= min(15, (40 - rsi) * 0.5)

        # MACD contribution
        if macd_hist > 0:
            score += min(15, abs(macd_hist) * 1000)
        else:
            score -= min(15, abs(macd_hist) * 1000)

        # Price vs SMA contribution
        score += 10 if price_vs_sma20 > 0 else -10
        score += 10 if price_vs_sma50 > 0 else -10

        score = max(5, min(95, round(score)))

        if score >= 80:
            label = "Strong Bullish"
            desc = "Indicators strongly align with a strong upward trend."
        elif score >= 60:
            label = "Bullish"
            desc = "Majority of indicators indicate an upward trend; watch for minor resistances."
        elif score >= 40:
            label = "Neutral"
            desc = "Mixed or conflicting signals; market trend is consolidated."
        elif score >= 20:
            label = "Bearish"
            desc = "Majority of indicators indicate a downward trend; caution is advised."
        else:
            label = "Strong Bearish"
            desc = "Indicators strongly align with a strong downward trend."

        return label, desc, score

    @staticmethod
    def analyze_multi_timeframe(close: pd.Series, df: pd.DataFrame) -> dict:
        """Runs trend and indicators over 1W, 1M, 3M, and 6M horizons."""
        timeframes = {
            "1W": 5,
            "1M": 21,
            "3M": 63,
            "6M": 126
        }
        res = {}
        for tf, days in timeframes.items():
            if len(df) < days + 5:
                res[tf] = {"Trend": "Insufficient Data", "Score": 50, "Return": "0.0%"}
                continue
            
            sub_close = close.iloc[-days:]
            start_price = sub_close.iloc[0]
            end_price = sub_close.iloc[-1]
            pct_return = ((end_price - start_price) / start_price) * 100
            
            # Simple technical proxy check for trend in this timeframe
            sma20 = TechnicalIndicatorService.calculate_sma(close, min(20, days)).iloc[-1]
            sub_rsi = TechnicalIndicatorService.calculate_rsi(close, min(14, days)).iloc[-1]
            
            tf_score = 50
            if end_price > sma20:
                tf_score += 15
            else:
                tf_score -= 15
                
            if sub_rsi > 55:
                tf_score += 10
            elif sub_rsi < 45:
                tf_score -= 10
                
            tf_score = max(10, min(90, tf_score))
            
            if tf_score >= 70:
                tf_trend = "Bullish"
            elif tf_score <= 30:
                tf_trend = "Bearish"
            else:
                tf_trend = "Neutral"
                
            res[tf] = {
                "Trend": tf_trend,
                "Score": tf_score,
                "Return": f"{pct_return:.1f}%"
            }
        return res

    @staticmethod
    def detect_conflicts_and_traps(rsi: float, macd_hist: float, price: float, sma20: float, sma50: float, bb_upper: float, bb_lower: float, volume_ratio: float, volume_signal: str) -> tuple:
        """Detects signal conflicts, risk traps (Bull/Bear), and breakout/breakdown probabilities."""
        conflicts = []
        
        # 1. Overbought RSI + Bullish MACD
        if rsi > 70 and macd_hist > 0:
            conflicts.append("Overbought RSI (>70) while MACD histogram remains positive. Momentum is strong but overextended.")
            
        # 2. Oversold RSI + Bearish Trend
        if rsi < 30 and price < sma50:
            conflicts.append("Oversold RSI (<30) within a primary bearish trend below SMA50. Risk of trend continuation remains high.")

        # 3. Bullish Price Action + Weak Volume
        if price > sma20 and volume_signal in ("WEAK", "BELOW_AVERAGE"):
            conflicts.append("Price trades above SMA20 but volume participation is below average, indicating weak conviction.")

        # 4. Bearish MACD + Price above SMA20
        if macd_hist < 0 and price > sma20:
            conflicts.append("MACD histogram is negative (bearish momentum) while price remains above SMA20 support.")

        # Traps
        bull_trap_risk = "Low"
        bear_trap_risk = "Low"
        
        # Bull Trap detection: price near upper band or making high on low volume with overbought RSI
        if price >= bb_upper * 0.98 and volume_ratio < 0.8 and rsi > 68:
            bull_trap_risk = "Elevated (Price hitting resistance on low volume and overbought conditions)"
            
        # Bear Trap detection: price near lower band on low volume with oversold RSI
        if price <= bb_lower * 1.02 and volume_ratio < 0.8 and rsi < 32:
            bear_trap_risk = "Elevated (Price at support on low volume and oversold conditions)"

        # Breakout/Breakdown Probabilities
        bb_width = (bb_upper - bb_lower) / price
        # Standard BB bandwidth indicator: small width means squeeze
        is_squeeze = bb_width < 0.08
        
        breakout_prob = 30 # baseline
        breakdown_prob = 30
        
        if is_squeeze:
            # Squeeze increases probability of both breakouts/breakdowns
            breakout_prob += 20
            breakdown_prob += 20
            
        # Directional bias based on price location and MACD
        if price > (bb_upper + bb_lower)/2:
            breakout_prob += 15
            if volume_ratio > 1.2:
                breakout_prob += 10
        else:
            breakdown_prob += 15
            if volume_ratio > 1.2:
                breakdown_prob += 10
                
        breakout_prob = min(85, breakout_prob)
        breakdown_prob = min(85, breakdown_prob)
        
        return conflicts, bull_trap_risk, bear_trap_risk, breakout_prob, breakdown_prob

    @classmethod
    def get_all_indicators(cls, df: pd.DataFrame) -> dict:
        """Upgraded main entry point to perform complete institutional technical analysis."""
        flags = []
        if df.empty:
            return {"error": "Empty dataframe provided.", "flags": ["NO_DATA"]}

        trading_days = len(df)
        if trading_days < 50:
            flags.append("INSUFFICIENT_DATA_MINIMUM_50_DAYS")

        close = df["Close"]
        current_price = round(close.iloc[-1], 2)

        # Basic Indicators
        rsi_series = cls.calculate_rsi(close)
        rsi = round(rsi_series.iloc[-1], 2) if not rsi_series.empty else 50.0

        macd_df = cls.calculate_macd(close)
        macd_line = round(macd_df["MACD"].iloc[-1], 4)
        macd_signal = round(macd_df["Signal"].iloc[-1], 4)
        macd_histogram = round(macd_df["Histogram"].iloc[-1], 4)

        bb = cls.calculate_bollinger_bands(close)
        bb_upper = round(bb["Upper"].iloc[-1], 2)
        bb_middle = round(bb["Middle"].iloc[-1], 2)
        bb_lower = round(bb["Lower"].iloc[-1], 2)

        atr = cls.calculate_atr(df)
        atr_14 = round(atr.iloc[-1], 2)

        sma20 = cls.calculate_sma(close, 20)
        sma50 = cls.calculate_sma(close, 50)
        ema12 = cls.calculate_ema(close, 12)
        ema26 = cls.calculate_ema(close, 26)

        sma20_val = round(sma20.iloc[-1], 2)
        sma50_val = round(sma50.iloc[-1], 2)
        ema12_val = round(ema12.iloc[-1], 2)
        ema26_val = round(ema26.iloc[-1], 2)

        price_vs_sma20 = current_price - sma20_val
        price_vs_sma50 = current_price - sma50_val

        # Volume & S&R
        volume_data = cls.analyze_volume(df)
        volume_ratio = volume_data.get("Volume_Ratio_to_Avg", 1.0)
        volume_signal = volume_data.get("Volume_Signal", "NEUTRAL")

        try:
            sr_levels = cls.calculate_support_resistance(df)
        except Exception:
            sr_levels = {}
            flags.append("SUPPORT_RESISTANCE_UNAVAILABLE")

        # Multi-timeframe
        timeframe_analysis = cls.analyze_multi_timeframe(close, df)

        # Trend Label & Score
        trend_label, trend_desc, trend_score = cls.classify_trend_score(
            rsi, macd_histogram, price_vs_sma20, price_vs_sma50
        )

        # Conflicts, Traps & Risk Signals
        conflicts, bull_trap_risk, bear_trap_risk, breakout_prob, breakdown_prob = cls.detect_conflicts_and_traps(
            rsi, macd_histogram, current_price, sma20_val, sma50_val, bb_upper, bb_lower, volume_ratio, volume_signal
        )

        # Trade Quality Score (0-100)
        # Higher score means indicators are highly aligned (strong bullish or strong bearish) on good volume
        alignment = abs(trend_score - 50) * 2  # Max 100
        vol_bonus = 10 if volume_ratio > 1.2 else -10
        conflict_penalty = len(conflicts) * 15
        
        trade_quality_score = max(10, min(95, round(alignment + vol_bonus - conflict_penalty)))

        # Confidence Score & Explanation (capped at 95.0%)
        conf_score = 90.0
        conf_breakdown = []

        if trading_days < 60:
            conf_score -= 25.0
            conf_breakdown.append("insufficient trading days (<60) -25")
        elif trading_days < 100:
            conf_score -= 10.0
            conf_breakdown.append("short history (<100) -10")
            
        if conflicts:
            penalty = len(conflicts) * 5.0
            conf_score -= penalty
            conf_breakdown.append(f"indicator conflicts -{penalty}")
            
        if volume_ratio < 0.6:
            conf_score -= 10.0
            conf_breakdown.append("extremely low volume -10")
            
        conf_score = min(conf_score, 95.0)
        conf_score = max(10.0, conf_score)

        explanation = (
            f"Confidence Score of {conf_score:.1f}% represents technical data reliability. "
            f"Deductions made due to: {', '.join(conf_breakdown) if conf_breakdown else 'no major indicator anomalies'}. "
            f"Maximum confidence is capped at 95.0% to account for market volatility."
        )

        # Interpretations
        if rsi > 70:
            rsi_interp = f"RSI({rsi}) indicates overbought levels. Consolidation risk is high."
        elif rsi < 30:
            rsi_interp = f"RSI({rsi}) indicates oversold levels. Short-term support bounce potential."
        else:
            rsi_interp = f"RSI({rsi}) is in the neutral range."

        if macd_histogram > 0:
            macd_interp = "MACD histogram is positive, indicating upward momentum."
        else:
            macd_interp = "MACD histogram is negative, indicating downward momentum."

        momentum_analysis = {
            "Price_vs_SMA20": f"{'+' if price_vs_sma20 >= 0 else ''}{price_vs_sma20:.2f} ({'Above' if price_vs_sma20 >= 0 else 'Below'} SMA20)",
            "Price_vs_SMA50": f"{'+' if price_vs_sma50 >= 0 else ''}{price_vs_sma50:.2f} ({'Above' if price_vs_sma50 >= 0 else 'Below'} SMA50)",
            "BB_Position": "Upper Band" if current_price > bb_upper * 0.98 else "Lower Band" if current_price < bb_lower * 1.02 else "Middle Band Range",
            "RSI_Interpretation": rsi_interp,
            "MACD_Interpretation": macd_interp
        }

        return {
            "current_price": current_price,
            "trading_days": trading_days,
            "indicators": {
                "RSI_14": rsi,
                "MACD_Line": macd_line,
                "MACD_Signal": macd_signal,
                "MACD_Histogram": macd_histogram,
                "SMA_20": sma20_val,
                "SMA_50": sma50_val,
                "EMA_12": ema12_val,
                "EMA_26": ema26_val,
                "Bollinger_Upper": bb_upper,
                "Bollinger_Middle": bb_middle,
                "Bollinger_Lower": bb_lower,
                "ATR_14": atr_14
            },
            "volume_analysis": volume_data,
            "support_resistance": sr_levels,
            "momentum_analysis": momentum_analysis,
            "multi_timeframe": timeframe_analysis,
            "trend": {
                "Trend_Label": trend_label,
                "Trend_Description": trend_desc,
                "Trend_Score": trend_score
            },
            "signal_conflicts": conflicts,
            "risk_signals": {
                "Bull_Trap_Risk": bull_trap_risk,
                "Bear_Trap_Risk": bear_trap_risk,
                "Breakout_Probability": f"{breakout_prob}%",
                "Breakdown_Probability": f"{breakdown_prob}%"
            },
            "trade_quality_score": trade_quality_score,
            "flags": flags,
            "confidence_score": conf_score,
            "confidence_explanation": explanation,
            "confidence_warning": conf_score < 70
        }
