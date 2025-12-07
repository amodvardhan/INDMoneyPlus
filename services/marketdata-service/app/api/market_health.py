"""Market health and condition endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import List, Optional
from app.core.database import get_db
from app.models.instrument import Instrument, PricePoint
from app.schemas.market_data import MarketHealthResponse, IndexHealth, MarketCondition
from app.core.adapters import MarketDataAdapter, InMemoryAdapter

router = APIRouter()

# Initialize adapter
_adapter: Optional[MarketDataAdapter] = None

def get_adapter() -> MarketDataAdapter:
    """Get market data adapter"""
    global _adapter
    if _adapter is None:
        from app.core.config import settings
        from app.core.adapters.yahoo_finance import YahooFinanceAdapter
        from app.core.adapters.tiingo import TiingoAdapter
        
        # Prefer Tiingo if API key is available
        if settings.tiingo_api_key and (settings.adapter_type == "tiingo" or settings.adapter_type == "auto"):
            _adapter = TiingoAdapter(api_key=settings.tiingo_api_key)
            logger.info("Using Tiingo adapter for real market data")
        elif settings.adapter_type == "yahoo_finance" or settings.adapter_type == "real":
            _adapter = YahooFinanceAdapter()
            logger.info("Using Yahoo Finance adapter for real market data")
        else:
            _adapter = InMemoryAdapter()
            logger.info("Using InMemory adapter (synthetic data)")
    return _adapter


@router.get("/market-health", response_model=MarketHealthResponse)
async def get_market_health(
    db: AsyncSession = Depends(get_db),
    adapter: MarketDataAdapter = Depends(get_adapter)
):
    """
    Get overall market health and condition.
    Analyzes major indices, volatility, and market sentiment.
    """
    try:
        # Get major indices (NSE Nifty 50, BSE Sensex, etc.)
        indices = [
            {"ticker": "NIFTY50", "exchange": "NSE", "name": "Nifty 50"},
            {"ticker": "SENSEX", "exchange": "BSE", "name": "Sensex"},
        ]
        
        index_healths = []
        total_change = 0
        total_volume = 0
        active_indices = 0
        
        for idx in indices:
            try:
                # Get latest price
                result = await db.execute(
                    select(Instrument).where(
                        Instrument.ticker == idx["ticker"],
                        Instrument.exchange == idx["exchange"]
                    )
                )
                instrument = result.scalar_one_or_none()
                
                if not instrument:
                    continue
                
                # Get latest and previous day prices
                now = datetime.utcnow()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                yesterday_start = today_start - timedelta(days=1)
                
                # Latest price
                latest_result = await db.execute(
                    select(PricePoint).where(
                        PricePoint.instrument_id == instrument.id,
                        PricePoint.timestamp >= today_start
                    ).order_by(PricePoint.timestamp.desc()).limit(1)
                )
                latest = latest_result.scalar_one_or_none()
                
                # Previous close
                prev_result = await db.execute(
                    select(PricePoint).where(
                        PricePoint.instrument_id == instrument.id,
                        PricePoint.timestamp < today_start,
                        PricePoint.timestamp >= yesterday_start
                    ).order_by(PricePoint.timestamp.desc()).limit(1)
                )
                prev_close = prev_result.scalar_one_or_none()
                
                if latest and prev_close:
                    current_price = latest.close
                    previous_price = prev_close.close
                    change = current_price - previous_price
                    change_percent = (change / previous_price * 100) if previous_price > 0 else 0
                    volume = latest.volume or 0
                    
                    # Determine trend
                    if change_percent > 1:
                        trend = "strong_bullish"
                    elif change_percent > 0.3:
                        trend = "bullish"
                    elif change_percent > -0.3:
                        trend = "neutral"
                    elif change_percent > -1:
                        trend = "bearish"
                    else:
                        trend = "strong_bearish"
                    
                    index_healths.append(IndexHealth(
                        name=idx["name"],
                        ticker=idx["ticker"],
                        exchange=idx["exchange"],
                        current_value=current_price,
                        change=change,
                        change_percent=change_percent,
                        volume=volume,
                        trend=trend
                    ))
                    
                    total_change += change_percent
                    total_volume += volume
                    active_indices += 1
                    
            except Exception as e:
                # Skip this index if there's an error
                continue
        
        # Calculate overall market condition
        if active_indices > 0:
            avg_change = total_change / active_indices
            
            # Determine market condition
            if avg_change > 2:
                condition = MarketCondition.STRONG_BULL
                health_score = min(100, 50 + (avg_change * 10))
                sentiment = "Very Positive"
            elif avg_change > 0.5:
                condition = MarketCondition.BULL
                health_score = min(100, 50 + (avg_change * 10))
                sentiment = "Positive"
            elif avg_change > -0.5:
                condition = MarketCondition.NEUTRAL
                health_score = 50
                sentiment = "Neutral"
            elif avg_change > -2:
                condition = MarketCondition.BEAR
                health_score = max(0, 50 + (avg_change * 10))
                sentiment = "Cautious"
            else:
                condition = MarketCondition.STRONG_BEAR
                health_score = max(0, 50 + (avg_change * 10))
                sentiment = "Negative"
        else:
            # Fallback if no index data
            condition = MarketCondition.NEUTRAL
            health_score = 50
            sentiment = "Data Unavailable"
            avg_change = 0
        
        # Calculate volatility (simplified - using price range)
        volatility = "Low"
        if abs(avg_change) > 2:
            volatility = "High"
        elif abs(avg_change) > 1:
            volatility = "Medium"
        
        return MarketHealthResponse(
            condition=condition,
            health_score=round(health_score, 2),
            sentiment=sentiment,
            overall_change_percent=round(avg_change, 2),
            volatility=volatility,
            indices=index_healths,
            last_updated=datetime.utcnow(),
            recommendation="Buy" if condition in [MarketCondition.BULL, MarketCondition.STRONG_BULL] else 
                          "Hold" if condition == MarketCondition.NEUTRAL else "Caution"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate market health: {str(e)}"
        )


@router.get("/price-comparison/{ticker}")
async def get_price_comparison(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    adapter: MarketDataAdapter = Depends(get_adapter)
):
    """
    Get price comparison across NSE and BSE for a ticker.
    Many stocks trade on both exchanges with slight price differences.
    """
    ticker_upper = ticker.upper()
    prices = {}
    
    for exchange in ["NSE", "BSE"]:
        try:
            result = await db.execute(
                select(Instrument).where(
                    Instrument.ticker == ticker_upper,
                    Instrument.exchange == exchange
                )
            )
            instrument = result.scalar_one_or_none()
            
            if instrument:
                # Get latest price
                latest_result = await db.execute(
                    select(PricePoint).where(
                        PricePoint.instrument_id == instrument.id
                    ).order_by(PricePoint.timestamp.desc()).limit(1)
                )
                latest = latest_result.scalar_one_or_none()
                
                if latest:
                    prices[exchange] = {
                        "price": latest.close,
                        "change": latest.close - latest.open,
                        "change_percent": ((latest.close - latest.open) / latest.open * 100) if latest.open > 0 else 0,
                        "volume": latest.volume,
                        "high": latest.high,
                        "low": latest.low,
                        "timestamp": latest.timestamp.isoformat()
                    }
        except Exception:
            continue
    
    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Price data not found for {ticker} on NSE or BSE"
        )
    
    # Calculate arbitrage opportunity if both exchanges have data
    arbitrage = None
    if "NSE" in prices and "BSE" in prices:
        nse_price = prices["NSE"]["price"]
        bse_price = prices["BSE"]["price"]
        diff = abs(nse_price - bse_price)
        diff_percent = (diff / min(nse_price, bse_price) * 100) if min(nse_price, bse_price) > 0 else 0
        
        arbitrage = {
            "difference": diff,
            "difference_percent": round(diff_percent, 2),
            "cheaper_exchange": "NSE" if nse_price < bse_price else "BSE",
            "opportunity": "Significant" if diff_percent > 0.5 else "Minor" if diff_percent > 0.1 else "None"
        }
    
    return {
        "ticker": ticker_upper,
        "prices": prices,
        "arbitrage": arbitrage,
        "recommendation": f"Consider buying on {arbitrage['cheaper_exchange']}" if arbitrage and arbitrage['opportunity'] != "None" else "Prices are similar across exchanges"
    }

