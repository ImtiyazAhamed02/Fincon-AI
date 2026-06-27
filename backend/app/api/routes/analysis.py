from fastapi import APIRouter, HTTPException
from app.schemas.requests import StockAnalysisRequest, PortfolioAnalysisRequest, NewsAnalysisRequest, TechnicalAnalysisRequest, RiskAnalysisRequest, FundamentalAnalysisRequest
from app.agents.crew import get_financial_crew
import traceback

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Full Multi-Agent Analysis (all 4 agents in sequence → CIO recommendation)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze/stock", summary="Full multi-agent stock analysis")
def analyze_stock(request: StockAnalysisRequest):
    """
    Runs the full 4-agent crew: News → Technical → Risk → Manager (CIO).
    Returns a consolidated investment recommendation.
    """
    try:
        crew = get_financial_crew()
        result = crew.analyze_stock(company=request.company_name, ticker=request.ticker)
        return {"status": "success", **result, "message": "Full analysis completed."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Individual Agent Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze/news", summary="News sentiment agent only")
def analyze_news(request: NewsAnalysisRequest):
    """
    Runs ONLY the News Analyst agent for a given ticker.
    Returns a sentiment analysis report.
    """
    try:
        crew = get_financial_crew()
        result = crew.analyze_news(ticker=request.ticker)
        return {"status": "success", **result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/technical", summary="Technical analysis agent only")
def analyze_technical(request: TechnicalAnalysisRequest):
    """
    Runs ONLY the Technical Analyst agent for a given ticker.
    Returns RSI, MACD, and trend analysis.
    """
    try:
        crew = get_financial_crew()
        result = crew.analyze_technical(ticker=request.ticker)
        return {"status": "success", **result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/risk", summary="Risk assessment agent only")
def analyze_risk(request: RiskAnalysisRequest):
    """
    Runs ONLY the Risk Officer agent for a given ticker.
    Returns a volatility and downside risk report.
    """
    try:
        crew = get_financial_crew()
        result = crew.analyze_risk(ticker=request.ticker)
        return {"status": "success", **result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/portfolio", summary="Portfolio manager agent only")
def analyze_portfolio(request: PortfolioAnalysisRequest = None):
    """
    Runs ONLY the Portfolio Manager agent for a given portfolio_id.
    Returns allocation and diversification review.
    """
    try:
        crew = get_financial_crew()
        p_id = request.portfolio_id if request else None
        result = crew.analyze_portfolio(portfolio_id=p_id)
        return {"status": "success", **result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/fundamental", summary="Fundamental analysis agent only")
def analyze_fundamental(request: FundamentalAnalysisRequest):
    """
    Runs ONLY the Fundamental Analyst agent for a given ticker.
    Returns corporate growth, health, and valuation metrics.
    """
    try:
        crew = get_financial_crew()
        result = crew.analyze_fundamental(ticker=request.ticker)
        return {"status": "success", **result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
