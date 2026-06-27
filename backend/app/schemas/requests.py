from pydantic import BaseModel, Field


class StockAnalysisRequest(BaseModel):
    company_name: str = Field(..., example="Apple Inc.")
    ticker: str = Field(..., example="AAPL")


class NewsAnalysisRequest(BaseModel):
    ticker: str = Field(..., example="AAPL")


class TechnicalAnalysisRequest(BaseModel):
    ticker: str = Field(..., example="AAPL")


class RiskAnalysisRequest(BaseModel):
    ticker: str = Field(..., example="AAPL")


class PortfolioAnalysisRequest(BaseModel):
    portfolio_id: str | None = Field(None, example="123e4567-e89b-12d3-a456-426614174000")


class FundamentalAnalysisRequest(BaseModel):
    ticker: str = Field(..., example="AAPL")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
