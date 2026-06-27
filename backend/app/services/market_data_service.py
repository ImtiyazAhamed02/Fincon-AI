import yfinance as yf
import pandas as pd
from datetime import datetime
from app.core.logger import logger

class MarketDataService:
    @staticmethod
    def get_historical_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetches historical price data using yfinance.
        Returns a pandas DataFrame.
        """
        try:
            logger.info(f"[MarketDataService] Fetching {period} of {interval} data for {ticker}")
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"[MarketDataService] No data found for {ticker}")
                return pd.DataFrame()
                
            # Drop timezone information for easier processing
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
                
            return df
        except Exception as e:
            logger.error(f"[MarketDataService] Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_current_info(ticker: str) -> dict:
        """
        Fetches current stock information (price, high/low, etc).
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
                "previous_close": info.get("previousClose"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "volume": info.get("volume"),
                "market_cap": info.get("marketCap")
            }
        except Exception as e:
            logger.error(f"[MarketDataService] Error fetching info for {ticker}: {e}")
            return {}
