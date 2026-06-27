from langchain_core.tools import Tool
import json
from datetime import datetime, timezone
from app.services.market_data_service import MarketDataService
from app.services.technical_indicator_service import TechnicalIndicatorService
from app.services.risk_metrics_service import RiskMetricsService
from app.services.sentiment_service import SentimentService
from app.services.fundamental_service import FundamentalService
from app.core.logger import logger

try:
    from crewai.tools import tool as crewai_tool
    HAS_CREWAI_TOOL = True
except ImportError:
    HAS_CREWAI_TOOL = False

def _create_tool(name: str, func, description: str):
    if HAS_CREWAI_TOOL:
        func.__name__ = name
        func.__doc__ = description
        return crewai_tool(name)(func)
    else:
        return Tool(name=name, func=func, description=description)

def _get_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def _get_stock_technical_data(ticker: str) -> str:
    try:
        logger.info(f"[Tools] Fetching institutional-grade technical data for {ticker}")
        df = MarketDataService.get_historical_data(ticker, period="3mo")
        if df.empty:
            return json.dumps({"error": f"No price data found for ticker {ticker}"})

        indicators = TechnicalIndicatorService.get_all_indicators(df)
        info = MarketDataService.get_current_info(ticker)

        result = {
            "symbol":           ticker,
            "current_data":     info,
            "technical_analysis": indicators,  # Full structured output from upgraded service
            "data_source":      "Yahoo Finance (yfinance)",
            "generated_at":     _get_timestamp(),
        }
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[Tools] Error fetching technical data for {ticker}: {e}")
        return json.dumps({"error": f"Internal computation error for {ticker}"})

get_stock_technical_data = _create_tool(
    name="get_stock_technical_data",
    func=_get_stock_technical_data,
    description=(
        "Fetches institutional-grade technical analysis for a stock ticker. Returns: "
        "RSI(14), MACD Line/Signal/Histogram, SMA20, SMA50, EMA12, EMA26, Bollinger Bands, ATR, "
        "Volume Analysis, Support/Resistance levels, Signal Conflicts, Trend Classification, "
        "Trend Score, Momentum Analysis, Confidence Score, and Data Flags. "
        "Input is just the ticker string (e.g. 'AAPL')."
    )
)

def _get_stock_news(ticker: str) -> str:
    try:
        logger.info(f"[Tools] Fetching quantitative news sentiment for {ticker}")
        sentiment_data = SentimentService.analyze_news(ticker)
        
        if "error" in sentiment_data:
            return json.dumps(sentiment_data)
            
        result = {
            "symbol": ticker,
            "sentiment_analysis": sentiment_data,
            "data_source": "Finnhub API",
            "generated_at": _get_timestamp()
        }
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[Tools] Error fetching news for {ticker}: {e}")
        return json.dumps({"error": f"Internal computation error for {ticker}"})

get_stock_news = _create_tool(
    name="get_stock_news",
    func=_get_stock_news,
    description="Fetches real-time live news and calculates deterministic Bullish/Bearish/Neutral sentiment scores for a stock ticker. Input is just the ticker string."
)

def _get_risk_metrics(ticker: str) -> str:
    try:
        logger.info(f"[Tools] Fetching institutional-grade risk metrics for {ticker}")
        result_data = RiskMetricsService.calculate_metrics(ticker)

        if not result_data or "error" in result_data:
            return json.dumps({"error": f"Not enough historical data to compute risk metrics for {ticker}"})

        result = {
            "symbol":           ticker,
            "risk_assessment":  result_data,   # Full structured output from upgraded service
            "data_source":      "Yahoo Finance (yfinance)",
            "generated_at":     _get_timestamp(),
        }
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[Tools] Error computing risk for {ticker}: {e}")
        return json.dumps({"error": f"Internal computation error for {ticker}"})

get_risk_metrics = _create_tool(
    name="get_risk_metrics",
    func=_get_risk_metrics,
    description=(
        "Fetches institutional-grade risk assessment for a stock ticker. Returns: "
        "Annualized Volatility, Beta, Alpha, Sharpe Ratio, Sortino Ratio, VaR (95%), CVaR, "
        "Max Drawdown, Benchmark Correlation, Risk Score (0-100), Risk Level (Low/Moderate/High/Very High), "
        "Confidence Score, VaR Interpretation, Methodology, and Data Quality Flags. "
        "Input is just the ticker string (e.g. 'AAPL')."
    )
)

def _get_portfolio_data(portfolio_id: str = None) -> str:
    from app.db.client import SQLiteClient
    try:
        # Standardize empty/null input from CrewAI agent calls
        if portfolio_id and str(portfolio_id).strip() not in ("", "None", "{}", "null", "undefined"):
            portfolios = SQLiteClient.execute("SELECT id, name FROM portfolios WHERE id = ?", (str(portfolio_id).strip(),))
        else:
            portfolios = SQLiteClient.execute("SELECT id, name FROM portfolios ORDER BY created_at DESC LIMIT 1")
            
        if not portfolios:
            return json.dumps({"error": "No portfolio available for analysis."})
            
        portfolio = portfolios[0]
        p_id = portfolio["id"]
        holdings = SQLiteClient.execute("SELECT ticker, shares, cost_basis FROM holdings WHERE portfolio_id = ?", (p_id,))
        
        result = {
            "name": portfolio["name"],
            "holdings": holdings
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Error fetching portfolio data: {str(e)}"})

get_portfolio_data = _create_tool(
    name="get_portfolio_data",
    func=_get_portfolio_data,
    description="Retrieves the holdings and asset list of the active investment portfolio. Can optionally accept a portfolio_id string."
)

def _get_stock_fundamental_data(ticker: str) -> str:
    try:
        logger.info(f"[Tools] Fetching institutional-grade fundamental data for {ticker}")
        fundamental_data = FundamentalService.get_fundamental_data(ticker)
        
        if "error" in fundamental_data:
            return json.dumps(fundamental_data)
            
        result = {
            "symbol": ticker,
            "fundamental_analysis": fundamental_data,
            "data_source": "Yahoo Finance (yfinance)",
            "generated_at": _get_timestamp()
        }
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[Tools] Error fetching fundamental data for {ticker}: {e}")
        return json.dumps({"error": f"Internal computation error for {ticker}"})

get_stock_fundamental_data = _create_tool(
    name="get_stock_fundamental_data",
    func=_get_stock_fundamental_data,
    description="Fetches institutional-grade fundamental and valuation data for a stock ticker. Input is just the ticker string."
)

