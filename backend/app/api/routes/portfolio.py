from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.client import SQLiteClient
import uuid
import traceback

router = APIRouter()

class PortfolioCreate(BaseModel):
    name: str

class HoldingCreate(BaseModel):
    ticker: str
    shares: float
    cost_basis: float

@router.get("", summary="Get all portfolios")
def get_portfolios():
    try:
        portfolios = SQLiteClient.execute("SELECT id, name, created_at FROM portfolios ORDER BY created_at DESC")
        return {"status": "success", "portfolios": portfolios}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", summary="Create a new portfolio")
def create_portfolio(payload: PortfolioCreate):
    try:
        portfolio_id = str(uuid.uuid4())
        SQLiteClient.execute_write(
            "INSERT INTO portfolios (id, user_id, name) VALUES (?, ?, ?)",
            (portfolio_id, "default_user", payload.name)
        )
        return {"status": "success", "id": portfolio_id, "name": payload.name}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{portfolio_id}", summary="Delete a portfolio")
def delete_portfolio(portfolio_id: str):
    try:
        # Delete portfolio (cascade deletes holdings)
        SQLiteClient.execute_write("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
        return {"status": "success", "message": f"Portfolio {portfolio_id} deleted."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{portfolio_id}/holdings", summary="Get holdings for a portfolio")
def get_holdings(portfolio_id: str):
    try:
        holdings = SQLiteClient.execute(
            "SELECT id, ticker, shares, cost_basis, created_at FROM holdings WHERE portfolio_id = ?",
            (portfolio_id,)
        )
        return {"status": "success", "holdings": holdings}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{portfolio_id}/holdings", summary="Add or update a holding")
def add_or_update_holding(portfolio_id: str, payload: HoldingCreate):
    try:
        ticker = payload.ticker.upper().strip()
        
        # Check if holding exists for this portfolio
        existing = SQLiteClient.execute(
            "SELECT id FROM holdings WHERE portfolio_id = ? AND ticker = ?",
            (portfolio_id, ticker)
        )
        
        if existing:
            # Update existing holding
            SQLiteClient.execute_write(
                "UPDATE holdings SET shares = ?, cost_basis = ? WHERE portfolio_id = ? AND ticker = ?",
                (payload.shares, payload.cost_basis, portfolio_id, ticker)
            )
            holding_id = existing[0]["id"]
        else:
            # Insert new holding
            holding_id = str(uuid.uuid4())
            SQLiteClient.execute_write(
                "INSERT INTO holdings (id, portfolio_id, ticker, shares, cost_basis) VALUES (?, ?, ?, ?, ?)",
                (holding_id, portfolio_id, ticker, payload.shares, payload.cost_basis)
            )
            
        return {
            "status": "success",
            "id": holding_id,
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "shares": payload.shares,
            "cost_basis": payload.cost_basis
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{portfolio_id}/holdings/{ticker}", summary="Delete a holding")
def delete_holding(portfolio_id: str, ticker: str):
    try:
        SQLiteClient.execute_write(
            "DELETE FROM holdings WHERE portfolio_id = ? AND ticker = ?",
            (portfolio_id, ticker.upper().strip())
        )
        return {"status": "success", "message": f"Holding {ticker} deleted from portfolio {portfolio_id}."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
