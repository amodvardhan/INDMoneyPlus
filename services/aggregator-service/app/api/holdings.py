"""Holdings endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from datetime import datetime
from app.core.database import get_db
from app.models.aggregator import BrokerAccount, NormalizedHolding
from app.schemas.aggregator import HoldingsResponse, ConsolidatedHolding

router = APIRouter()


@router.get("/{user_id}", response_model=HoldingsResponse)
async def get_consolidated_holdings(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get consolidated holdings for a user across all accounts"""
    # Get all accounts for user
    result = await db.execute(
        select(BrokerAccount).where(BrokerAccount.user_id == user_id)
    )
    accounts = result.scalars().all()
    
    if not accounts:
        return HoldingsResponse(
            user_id=user_id,
            holdings=[],
            total_valuation=None,
            last_updated=datetime.utcnow()
        )
    
    account_ids = [acc.id for acc in accounts]
    
    # Get all holdings for these accounts
    result = await db.execute(
        select(NormalizedHolding).where(
            NormalizedHolding.account_id.in_(account_ids)
        )
    )
    all_holdings = result.scalars().all()
    
    # Group by instrument (isin + ticker + exchange)
    holdings_by_instrument: Dict[str, List[NormalizedHolding]] = {}
    
    for holding in all_holdings:
        # Create key for grouping
        key_parts = []
        if holding.isin:
            key_parts.append(f"isin:{holding.isin}")
        if holding.ticker:
            key_parts.append(f"ticker:{holding.ticker}")
        if holding.exchange:
            key_parts.append(f"exchange:{holding.exchange}")
        
        if not key_parts:
            continue  # Skip holdings without identifier
        
        key = "|".join(key_parts)
        
        if key not in holdings_by_instrument:
            holdings_by_instrument[key] = []
        holdings_by_instrument[key].append(holding)
    
    # Consolidate holdings
    consolidated: List[ConsolidatedHolding] = []
    total_valuation = 0.0
    
    for key, holdings in holdings_by_instrument.items():
        # Use first holding as reference
        ref_holding = holdings[0]
        
        # Sum quantities and calculate weighted average price
        total_qty = sum(h.qty for h in holdings)
        
        # Calculate weighted average price
        total_cost = 0.0
        total_qty_for_avg = 0.0
        for h in holdings:
            if h.avg_price and h.qty > 0:
                total_cost += h.avg_price * h.qty
                total_qty_for_avg += h.qty
        
        avg_price = total_cost / total_qty_for_avg if total_qty_for_avg > 0 else None
        
        # Sum valuations
        total_val = sum(h.valuation for h in holdings if h.valuation)
        if total_val:
            total_valuation += total_val
        
        # Get account details
        account_details = []
        for h in holdings:
            result = await db.execute(
                select(BrokerAccount).where(BrokerAccount.id == h.account_id)
            )
            account = result.scalar_one()
            account_details.append({
                "account_id": h.account_id,
                "broker_name": account.broker_name,
                "qty": h.qty,
                "avg_price": h.avg_price,
                "valuation": h.valuation,
            })
        
        consolidated.append(ConsolidatedHolding(
            instrument_id=ref_holding.instrument_id,
            isin=ref_holding.isin,
            ticker=ref_holding.ticker,
            exchange=ref_holding.exchange,
            total_qty=total_qty,
            avg_price=avg_price,
            total_valuation=total_val if total_val else None,
            accounts=account_details
        ))
    
    # Get last updated timestamp
    if all_holdings:
        last_updated = max(h.updated_at for h in all_holdings)
    else:
        last_updated = datetime.utcnow()
    
    return HoldingsResponse(
        user_id=user_id,
        holdings=consolidated,
        total_valuation=total_valuation if total_valuation > 0 else None,
        last_updated=last_updated
    )

