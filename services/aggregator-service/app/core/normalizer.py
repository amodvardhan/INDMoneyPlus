"""Instrument normalization utilities"""
import httpx
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.aggregator import InstrumentMapping

logger = logging.getLogger(__name__)


class InstrumentNormalizer:
    """Normalize instruments using ISIN/Ticker mapping and marketdata service"""
    
    def __init__(self):
        self._cache = {}  # Cache for instrument lookups
    
    async def normalize_instrument(
        self,
        db: AsyncSession,
        ticker: Optional[str] = None,
        isin: Optional[str] = None,
        exchange: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize instrument by finding matching instrument_id.
        
        Returns:
            Dict with instrument_id, isin, ticker, exchange or None if not found
        """
        if not ticker and not isin:
            return None
        
        # Check cache first
        cache_key = (ticker or "", isin or "", exchange or "")
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try to find in mapping table
        result = None
        
        if isin:
            # Search by ISIN first
            query = select(InstrumentMapping).where(InstrumentMapping.isin == isin.upper())
            db_result = await db.execute(query)
            mapping = db_result.scalar_one_or_none()
            if mapping and mapping.instrument_id:
                result = {
                    "instrument_id": mapping.instrument_id,
                    "isin": mapping.isin,
                    "ticker": mapping.ticker,
                    "exchange": mapping.exchange,
                }
        
        if not result and ticker and exchange:
            # Search by ticker and exchange
            query = select(InstrumentMapping).where(
                InstrumentMapping.ticker == ticker.upper(),
                InstrumentMapping.exchange == exchange.upper()
            )
            db_result = await db.execute(query)
            mapping = db_result.scalar_one_or_none()
            if mapping and mapping.instrument_id:
                result = {
                    "instrument_id": mapping.instrument_id,
                    "isin": mapping.isin,
                    "ticker": mapping.ticker,
                    "exchange": mapping.exchange,
                }
        
        # If not found in mapping, try marketdata service
        if not result:
            result = await self._lookup_from_marketdata(ticker, isin, exchange)
            
            # If found, create mapping entry
            if result and result.get("instrument_id"):
                mapping = InstrumentMapping(
                    isin=result.get("isin"),
                    ticker=result.get("ticker", ""),
                    exchange=result.get("exchange", ""),
                    instrument_id=result.get("instrument_id")
                )
                db.add(mapping)
                await db.commit()
        
        # Cache result
        if result:
            self._cache[cache_key] = result
        
        return result
    
    async def _lookup_from_marketdata(
        self,
        ticker: Optional[str],
        isin: Optional[str],
        exchange: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Lookup instrument from marketdata service"""
        try:
            async with httpx.AsyncClient() as client:
                # Try by ticker and exchange first
                if ticker and exchange:
                    response = await client.get(
                        f"{settings.marketdata_service_url}/api/v1/instruments/{ticker}",
                        params={"exchange": exchange},
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "instrument_id": data.get("id"),
                            "isin": data.get("isin"),
                            "ticker": data.get("ticker"),
                            "exchange": data.get("exchange"),
                        }
                
                # Try search if ticker/exchange lookup fails
                if ticker:
                    response = await client.get(
                        f"{settings.marketdata_service_url}/api/v1/instruments",
                        params={"search": ticker},
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        instruments = response.json()
                        for inst in instruments:
                            if inst.get("ticker", "").upper() == ticker.upper():
                                return {
                                    "instrument_id": inst.get("id"),
                                    "isin": inst.get("isin"),
                                    "ticker": inst.get("ticker"),
                                    "exchange": inst.get("exchange"),
                                }
        except Exception as e:
            logger.error(f"Error looking up instrument from marketdata service: {e}")
        
        return None

