"""
Analytics Service - Portfolio calculations, XIRR, risk metrics
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import numpy as np
import pandas as pd

app = FastAPI(
    title="Analytics Service",
    description="Portfolio analytics, XIRR calculations, and risk metrics",
    version="0.1.0"
)

class CashFlow(BaseModel):
    date: date
    amount: float

class XIRRRequest(BaseModel):
    cash_flows: List[CashFlow]
    present_value: float

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "analytics-service"}

@app.post("/api/v1/analytics/xirr")
async def calculate_xirr(request: XIRRRequest):
    """Calculate XIRR (Extended Internal Rate of Return)"""
    try:
        # Convert to pandas for calculation
        dates = [cf.date for cf in request.cash_flows]
        amounts = [cf.amount for cf in request.cash_flows]
        
        # Add present value as final cash flow
        dates.append(date.today())
        amounts.append(-request.present_value)
        
        # Simple XIRR calculation (would use proper library in production)
        # This is a placeholder - use numpy_financial or similar
        xirr = 0.0  # TODO: Implement actual XIRR calculation
        
        return {
            "xirr": xirr,
            "cash_flows": len(request.cash_flows),
            "present_value": request.present_value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/analytics/portfolio-value")
async def calculate_portfolio_value(holdings: List[dict]):
    """Calculate total portfolio value"""
    total_value = sum(h.get("quantity", 0) * h.get("price", 0) for h in holdings)
    return {"total_value": total_value, "holdings_count": len(holdings)}

@app.post("/api/v1/analytics/risk-metrics")
async def calculate_risk_metrics(returns: List[float]):
    """Calculate risk metrics (Sharpe ratio, volatility, etc.)"""
    if not returns:
        raise HTTPException(status_code=400, detail="Returns list cannot be empty")
    
    returns_array = np.array(returns)
    volatility = np.std(returns_array) * np.sqrt(252)  # Annualized
    sharpe_ratio = (np.mean(returns_array) * 252) / volatility if volatility > 0 else 0
    
    return {
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe_ratio),
        "mean_return": float(np.mean(returns_array))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

