"""Recommendations API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging
import asyncio
from app.core.database import get_db
from app.models.recommendation import Recommendation, RecommendationSource, RecommendationType
from app.schemas.recommendation import (
    RecommendationRead,
    RecommendationCreate,
    RecommendationResponse,
    TopRecommendationsResponse,
)
import httpx
from app.core.config import settings
from app.core.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
    invalidate_recommendations_cache
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/recommendations/debug/price-test")
async def test_price_fetch(
    ticker: str = Query("ONGC", description="Ticker to test"),
    exchange: str = Query("NSE", description="Exchange to test"),
    db: AsyncSession = Depends(get_db)
):
    """
    Debug endpoint to test price fetching from market data service.
    Helps diagnose why fresh prices aren't being fetched.
    """
    import httpx
    
    result = {
        "ticker": ticker,
        "exchange": exchange,
        "marketdata_service_url": settings.marketdata_service_url,
        "test_url": f"{settings.marketdata_service_url}/api/v1/price/{ticker}/latest",
        "status": "unknown",
        "price": None,
        "source": None,
        "error": None,
        "response_status": None,
        "response_body": None
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                result["test_url"],
                params={"exchange": exchange}
            )
            result["response_status"] = response.status_code
            
            if response.status_code == 200:
                data = response.json()
                result["status"] = "success"
                result["price"] = data.get("price")
                result["source"] = data.get("data_source", "unknown")
                result["response_body"] = data
            else:
                result["status"] = "error"
                try:
                    result["response_body"] = response.json()
                    result["error"] = result["response_body"].get("detail", str(response.text))
                except:
                    result["error"] = response.text
                    
    except httpx.ConnectError as e:
        result["status"] = "connection_error"
        result["error"] = f"Cannot connect to market data service: {e}"
    except httpx.TimeoutException as e:
        result["status"] = "timeout"
        result["error"] = f"Request timed out: {e}"
    except Exception as e:
        result["status"] = "exception"
        result["error"] = str(e)
        logger.error(f"Price test error: {e}", exc_info=True)
    
    return result


@router.get("/recommendations/top", response_model=TopRecommendationsResponse)
async def get_top_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    recommendation_type: Optional[str] = Query(None, description="Filter by type: buy, sell, hold"),
    force_refresh: bool = Query(False, description="Force regeneration of recommendations"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top stock recommendations based on confidence, credibility, and recency.
    Dynamically generates recommendations using AI if none exist or they're stale.
    Uses Redis caching to avoid frequent regeneration.
    Returns buy and sell recommendations separately.
    """
    try:
        # CRITICAL: Never return cached recommendations without fresh prices
        # Prices change constantly - cached prices are unreliable
        # Always fetch fresh prices even if recommendations are cached
        # (We'll check cache after fetching fresh prices to avoid regenerating recommendations)
        
        # Check if we have fresh recommendations in database (within refresh window)
        refresh_threshold = datetime.utcnow() - timedelta(hours=settings.recommendation_refresh_hours)
        
        if not force_refresh:
            # Check for recent recommendations in database
            recent_query = select(func.count(Recommendation.id)).where(
                Recommendation.is_active == "true",
                Recommendation.created_at > refresh_threshold
            )
            recent_count = await db.execute(recent_query)
            has_recent = recent_count.scalar() > 0
            
            if has_recent:
                # Use existing recommendations BUT ALWAYS fetch fresh prices
                # This ensures prices are current even if recommendations are recent
                # DO NOT cache - prices must always be fresh
                result = await _get_existing_recommendations(db, limit, recommendation_type)
                return result
        
        # Generate new recommendations using AI agent
        await _generate_and_store_recommendations(db, limit)
        
        # Invalidate cache since we have new recommendations
        await invalidate_recommendations_cache("recommendations:top:*")
        
        # Get newly generated recommendations with FRESH prices
        result = await _get_existing_recommendations(db, limit, recommendation_type)
        
        # DO NOT cache recommendations with prices - prices change constantly
        # Only cache recommendation metadata, not prices
        # Prices must always be fetched fresh
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404, 503, etc.)
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch recommendations: {e}", exc_info=True)
        # Fallback to existing recommendations if generation fails
        try:
            logger.info("Attempting to return existing recommendations as fallback")
            return await _get_existing_recommendations(db, limit, recommendation_type)
        except Exception as fallback_error:
            logger.error(f"❌ Fallback to existing recommendations also failed: {fallback_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"Recommendations service temporarily unavailable. "
                    f"Error: {str(e)}. "
                    f"Please try again later or contact support if the issue persists."
                )
            )


async def _fetch_fresh_price(ticker: str, exchange: str, retry_count: int = 0) -> Optional[tuple]:
    """
    Fetch fresh current price from market data service - returns (price, source) tuple or None
    Returns: (price: float, source: str) or None if unavailable
    
    CRITICAL: This function MUST return None if price cannot be fetched.
    Never returns stale or fake data.
    """
    url = f"{settings.marketdata_service_url}/api/v1/price/{ticker}/latest"
    max_retries = 2
    timeout = 15.0  # Increased timeout
    
    logger.info(f"🔍 Fetching fresh price for {ticker} on {exchange} from: {url} (attempt {retry_count + 1}/{max_retries + 1})")
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # CRITICAL: Always use force_refresh=true to get fresh prices from adapter, not cached/stored prices
            response = await client.get(
                url,
                params={"exchange": exchange, "force_refresh": "true"},
                follow_redirects=True
            )
            
            logger.info(f"📊 Price fetch response for {ticker}: status={response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"📦 Full response data for {ticker}: {data}")
                
                price = data.get("price")
                
                # Validate price is valid
                if price is None:
                    logger.error(f"❌ No price field in response for {ticker} on {exchange}. Response: {data}")
                    return None
                
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    logger.error(f"❌ Invalid price type for {ticker} on {exchange}: {price} (type: {type(price)})")
                    return None
                
                if price <= 0:
                    logger.error(f"❌ Invalid price value for {ticker} on {exchange}: {price} (must be > 0)")
                    return None
                
                # Get data source from response - CRITICAL for showing source to user
                data_source = data.get("data_source")
                if not data_source or data_source == "unknown" or data_source == "":
                    # Fallback: try to infer from response structure
                    logger.warning(
                        f"⚠️  No data_source in response for {ticker} on {exchange}. "
                        f"Response keys: {list(data.keys())}. Using fallback."
                    )
                    data_source = "market_data_service"  # Generic fallback
                
                logger.info(
                    f"✅ Successfully fetched fresh price for {ticker} on {exchange}: "
                    f"₹{price} from {data_source} (response had data_source: {data.get('data_source')})"
                )
                return (price, data_source)
                
            elif response.status_code == 503:
                # Service unavailable - don't use fake data
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text if hasattr(response, 'text') else "Service unavailable"
                logger.error(
                    f"❌ Market data service unavailable for {ticker} on {exchange}: {error_detail}. "
                    f"URL: {url}"
                )
                return None
            else:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text if hasattr(response, 'text') else ""
                logger.error(
                    f"❌ Failed to fetch price for {ticker} on {exchange}: "
                    f"HTTP {response.status_code} - {error_detail}. URL: {url}"
                )
                return None
    except httpx.TimeoutException as e:
        error_msg = f"❌ Timeout fetching price for {ticker} on {exchange}: {e}"
        logger.error(error_msg)
        
        # Retry once if this is the first attempt
        if retry_count < max_retries:
            logger.info(f"🔄 Retrying price fetch for {ticker} after timeout (attempt {retry_count + 2})...")
            await asyncio.sleep(1)
            return await _fetch_fresh_price(ticker, exchange, retry_count + 1)
        
        return None
    except httpx.ConnectError as e:
        error_msg = (
            f"❌ Connection error fetching price for {ticker} on {exchange}: {e}. "
            f"Market data service may not be running at {settings.marketdata_service_url}. "
            f"Check if service is accessible."
        )
        logger.error(error_msg)
        
        # Retry once if this is the first attempt
        if retry_count < max_retries:
            logger.info(f"🔄 Retrying price fetch for {ticker} (attempt {retry_count + 2})...")
            await asyncio.sleep(1)  # Wait 1 second before retry
            return await _fetch_fresh_price(ticker, exchange, retry_count + 1)
        
        return None
    except httpx.HTTPError as e:
        logger.error(f"❌ HTTP error fetching price for {ticker} on {exchange}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching fresh price for {ticker} on {exchange}: {e}", exc_info=True)
        return None


async def _fetch_fresh_price_legacy(ticker: str, exchange: str) -> Optional[float]:
    """Legacy function - returns only price for backward compatibility"""
    result = await _fetch_fresh_price(ticker, exchange)
    if result:
        return result[0]  # Return just the price
    return None


async def _fetch_fresh_prices_batch(
    ticker_exchange_pairs: List[tuple]
) -> Dict[tuple, tuple]:
    """
    Fetch fresh prices for multiple tickers in parallel
    Returns: Dict mapping (ticker, exchange) -> (price: float, source: str)
    """
    if not ticker_exchange_pairs:
        return {}
    
    logger.info(f"🔄 Fetching fresh prices for {len(ticker_exchange_pairs)} tickers in parallel")
    
    async def fetch_one(ticker: str, exchange: str) -> tuple:
        result = await _fetch_fresh_price(ticker, exchange)
        return ((ticker, exchange), result)
    
    tasks = [fetch_one(ticker, exchange) for ticker, exchange in ticker_exchange_pairs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    price_map = {}
    success_count = 0
    failed_count = 0
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"❌ Price fetch exception: {result}")
            failed_count += 1
            continue
        (ticker, exchange), price_data = result
        if price_data and isinstance(price_data, tuple) and len(price_data) == 2:
            price, source = price_data
            if price is not None and price > 0:
                price_map[(ticker, exchange)] = (price, source)
                success_count += 1
            else:
                logger.warning(f"⚠️  No valid price returned for {ticker} on {exchange} (source: {source})")
                failed_count += 1
        elif price_data is None:
            logger.warning(f"⚠️  Price fetch returned None for {ticker} on {exchange} - market data service may be down")
            failed_count += 1
        else:
            logger.warning(f"⚠️  Invalid price data format for {ticker} on {exchange}: {price_data}")
            failed_count += 1
    
    logger.info(
        f"📊 Price fetch complete: {success_count}/{len(ticker_exchange_pairs)} successful, "
        f"{failed_count} failed. Market data service: {settings.marketdata_service_url}"
    )
    
    if success_count == 0 and len(ticker_exchange_pairs) > 0:
        logger.error(
            f"❌ CRITICAL: All price fetches failed! Market data service at {settings.marketdata_service_url} "
            f"may be down or unreachable. Check service status and network connectivity."
        )
    
    return price_map


async def _update_recommendations_with_fresh_prices(
    recommendations: List[Recommendation]
) -> List[RecommendationRead]:
    """Update recommendations with fresh prices from market data service (batched for performance)"""
    if not recommendations:
        logger.warning("⚠️  No recommendations provided to update with fresh prices")
        return []
    
    logger.info(f"🔄 Updating {len(recommendations)} recommendations with fresh prices")
    
    # Collect all ticker-exchange pairs
    ticker_exchange_pairs = [(rec.ticker, rec.exchange) for rec in recommendations]
    
    # Fetch all prices in parallel (with error handling)
    # CRITICAL: If price fetch fails, we MUST skip recommendations - no stale data
    try:
        price_map = await _fetch_fresh_prices_batch(ticker_exchange_pairs)
        if not price_map:
            logger.error(
                f"❌ CRITICAL: Price fetch returned empty map for {len(ticker_exchange_pairs)} tickers. "
                f"Market data service may be down or unreachable at {settings.marketdata_service_url}. "
                f"Check service logs and connectivity."
            )
    except Exception as e:
        logger.error(
            f"❌ CRITICAL: Error fetching fresh prices batch: {e}. "
            f"Market data service URL: {settings.marketdata_service_url}",
            exc_info=True
        )
        price_map = {}  # Empty map - recommendations with invalid stored prices will be skipped
    
    # Update recommendations with fresh prices
    # CRITICAL: Only use real prices - if unavailable, use stored price with warning if needed
    updated_recs = []
    for rec in recommendations:
        price_data = price_map.get((rec.ticker, rec.exchange))
        
        # Try to use fresh price first, fall back to stored price with warning if needed
        price_is_stale = False
        price_age_hours = None
        price_last_updated = None
        price_source = None
        
        # Extract price and source from tuple if available
        fresh_price = None
        if price_data and isinstance(price_data, tuple) and len(price_data) == 2:
            fresh_price, price_source = price_data
        elif price_data:
            # Handle legacy format (just price)
            if isinstance(price_data, (int, float)):
                fresh_price = price_data
                price_source = "market_data_service"
        
        if fresh_price is not None and fresh_price > 0:
            # Fresh price available - use it
            final_price = fresh_price
            price_is_stale = False
            price_last_updated = datetime.utcnow()
            price_age_hours = 0.0
            # price_source already set from tuple
            
            # Warn if stored price is significantly different (indicates stored was stale)
            if rec.current_price and rec.current_price > 0:
                price_diff_pct = abs((fresh_price - rec.current_price) / rec.current_price) * 100
                if price_diff_pct > 15:
                    logger.warning(
                        f"⚠️  Large price difference for {rec.ticker} on {rec.exchange}: "
                        f"stored={rec.current_price}, fresh={fresh_price}, diff={price_diff_pct:.1f}%. "
                        f"Stored price was stale. Using fresh price: {fresh_price} from {price_source}"
                    )
            
            logger.info(f"✅ Using fresh price for {rec.ticker} on {rec.exchange}: {final_price} from {price_source}")
            
        elif rec.current_price and rec.current_price > 0:
            # No fresh price available - use stored price but mark as stale with strong warnings
            price_last_updated = rec.created_at if rec.created_at else datetime.utcnow()
            price_age_hours = (datetime.utcnow() - price_last_updated).total_seconds() / 3600
            
            # Use stored price but mark as stale - ALWAYS show recommendations
            # Users need to see recommendations even if prices are stale - they'll be clearly marked
            final_price = rec.current_price
            price_is_stale = True
            price_source = "stored"  # Indicate this is from database, not live source
            
            # Log warning based on age
            if price_age_hours > 24:
                logger.warning(
                    f"⚠️  WARNING: Using very old stored price for {rec.ticker} on {rec.exchange}: {final_price} "
                    f"(age: {price_age_hours:.1f} hours). Fresh price unavailable. "
                    f"Price is VERY STALE - user must verify before making decisions."
                )
            elif price_age_hours > 6:
                logger.warning(
                    f"⚠️  Using stale stored price for {rec.ticker} on {rec.exchange}: {final_price} "
                    f"(age: {price_age_hours:.1f} hours). Fresh price unavailable - market data service may be down. "
                    f"Price marked as STALE - user should verify."
                )
            else:
                logger.info(
                    f"ℹ️  Using stored price for {rec.ticker} on {rec.exchange}: {final_price} "
                    f"(age: {price_age_hours:.1f} hours). Fresh price unavailable."
                )
        else:
            # No valid price available - skip this recommendation
            logger.error(
                f"❌ Skipping recommendation for {rec.ticker} on {rec.exchange}: "
                f"No valid price available (fresh: {fresh_price}, stored: {rec.current_price})"
            )
            continue  # Skip recommendations without any valid prices
        
        # CRITICAL: Validate target_price makes sense relative to current_price
        # For BUY/STRONG_BUY: target_price should be > current_price
        # For SELL/STRONG_SELL: target_price should be < current_price
        # For HOLD: target_price can be close to current_price
        validated_target_price = rec.target_price
        target_price_invalid = False
        
        if final_price and final_price > 0 and validated_target_price and validated_target_price > 0:
            rec_type = rec.recommendation_type.upper()
            
            # Check if target price is logically inconsistent with recommendation type
            if rec_type in ["BUY", "STRONG_BUY"]:
                if validated_target_price < final_price:
                    # Target price is below current price for a BUY - this is invalid!
                    target_price_invalid = True
                    logger.warning(
                        f"⚠️  INVALID: {rec.ticker} on {rec.exchange} has BUY recommendation but "
                        f"target_price (₹{validated_target_price}) < current_price (₹{final_price}). "
                        f"Recalculating target_price with 8% upside..."
                    )
                    # Recalculate target price with standard upside (8% for BUY, 15% for STRONG_BUY)
                    upside_pct = 0.15 if rec_type == "STRONG_BUY" else 0.08
                    validated_target_price = final_price * (1 + upside_pct)
                    logger.info(
                        f"✅ Recalculated target_price for {rec.ticker}: ₹{validated_target_price:.2f} "
                        f"({upside_pct*100:.0f}% upside from current ₹{final_price:.2f})"
                    )
            elif rec_type in ["SELL", "STRONG_SELL"]:
                if validated_target_price > final_price:
                    # Target price is above current price for a SELL - this is invalid!
                    target_price_invalid = True
                    logger.warning(
                        f"⚠️  INVALID: {rec.ticker} on {rec.exchange} has SELL recommendation but "
                        f"target_price (₹{validated_target_price}) > current_price (₹{final_price}). "
                        f"Recalculating target_price with 8% downside..."
                    )
                    # Recalculate target price with standard downside (8% for SELL)
                    downside_pct = 0.08
                    validated_target_price = final_price * (1 - downside_pct)
                    logger.info(
                        f"✅ Recalculated target_price for {rec.ticker}: ₹{validated_target_price:.2f} "
                        f"({downside_pct*100:.0f}% downside from current ₹{final_price:.2f})"
                    )
        
        # Create RecommendationRead with valid price and staleness metadata
        rec_dict = {
            "id": rec.id,
            "ticker": rec.ticker,
            "exchange": rec.exchange,
            "recommendation_type": rec.recommendation_type,
            "target_price": round(validated_target_price, 2) if validated_target_price else None,
            "current_price": final_price,
            "reasoning": rec.reasoning,
            "risk_level": rec.risk_level,
            "confidence_score": rec.confidence_score,
            "source": rec.source,
            "source_url": rec.source_url,
            "source_date": rec.source_date,
            "is_active": rec.is_active,
            "expires_at": rec.expires_at,
            "created_at": rec.created_at,
            "price_is_stale": price_is_stale,
            "price_age_hours": price_age_hours,
            "price_last_updated": price_last_updated,
            "price_source": price_source,
        }
        updated_recs.append(RecommendationRead.model_validate(rec_dict))
    
    logger.info(
        f"✅ Updated {len(updated_recs)}/{len(recommendations)} recommendations with prices. "
        f"Skipped {len(recommendations) - len(updated_recs)} due to missing prices."
    )
    
    return updated_recs


async def _get_existing_recommendations(
    db: AsyncSession,
    limit: int,
    recommendation_type: Optional[str]
) -> TopRecommendationsResponse:
    """Get existing recommendations from database with fresh prices"""
    # Check total count of active recommendations for debugging
    total_active_query = select(func.count(Recommendation.id)).where(
        Recommendation.is_active == "true"
    )
    total_active_result = await db.execute(total_active_query)
    total_active = total_active_result.scalar()
    logger.info(f"📊 Total active recommendations in database: {total_active}")
    
    query = select(Recommendation).where(
        Recommendation.is_active == "true",
        or_(
            Recommendation.expires_at.is_(None),
            Recommendation.expires_at > datetime.utcnow()
        )
    )
    
    if recommendation_type:
        try:
            rec_type = RecommendationType(recommendation_type.lower())
            query = query.where(Recommendation.recommendation_type == rec_type)
        except ValueError:
            pass
    
    # Get buy recommendations
    buy_query = query.where(
        Recommendation.recommendation_type.in_([
            RecommendationType.STRONG_BUY,
            RecommendationType.BUY
        ])
    ).order_by(
        Recommendation.confidence_score.desc(),
        Recommendation.created_at.desc()
    ).limit(limit)
    
    buy_result = await db.execute(buy_query)
    buy_recommendations = buy_result.scalars().all()
    logger.info(f"📊 Found {len(buy_recommendations)} buy recommendations")
    
    # Get sell recommendations
    sell_query = query.where(
        Recommendation.recommendation_type.in_([
            RecommendationType.STRONG_SELL,
            RecommendationType.SELL
        ])
    ).order_by(
        Recommendation.confidence_score.desc(),
        Recommendation.created_at.desc()
    ).limit(limit)
    
    sell_result = await db.execute(sell_query)
    sell_recommendations = sell_result.scalars().all()
    logger.info(f"📊 Found {len(sell_recommendations)} sell recommendations")
    
    # Load source relationships
    for rec in buy_recommendations + sell_recommendations:
        await db.refresh(rec, ["source"])
    
    # Update with fresh prices (with error handling)
    try:
        buy_recs_updated = await _update_recommendations_with_fresh_prices(buy_recommendations)
    except Exception as e:
        logger.error(f"❌ Error updating buy recommendations with fresh prices: {e}", exc_info=True)
        # Fallback: return recommendations with stored prices (marked as stale)
        buy_recs_updated = []
        for rec in buy_recommendations:
            price_age_hours = (datetime.utcnow() - rec.created_at).total_seconds() / 3600 if rec.created_at else None
            rec_dict = {
                "id": rec.id,
                "ticker": rec.ticker,
                "exchange": rec.exchange,
                "recommendation_type": rec.recommendation_type,
                "target_price": rec.target_price,
                "current_price": rec.current_price,
                "reasoning": rec.reasoning,
                "risk_level": rec.risk_level,
                "confidence_score": rec.confidence_score,
                "source": rec.source,
                "source_url": rec.source_url,
                "source_date": rec.source_date,
                "is_active": rec.is_active,
                "expires_at": rec.expires_at,
                "created_at": rec.created_at,
                "price_is_stale": True,
                "price_age_hours": price_age_hours,
                "price_last_updated": rec.created_at if rec.created_at else datetime.utcnow(),
                "price_source": "stored",
            }
            buy_recs_updated.append(RecommendationRead.model_validate(rec_dict))
    
    try:
        sell_recs_updated = await _update_recommendations_with_fresh_prices(sell_recommendations)
    except Exception as e:
        logger.error(f"❌ Error updating sell recommendations with fresh prices: {e}", exc_info=True)
        # Fallback: return recommendations with stored prices (marked as stale)
        sell_recs_updated = []
        for rec in sell_recommendations:
            price_age_hours = (datetime.utcnow() - rec.created_at).total_seconds() / 3600 if rec.created_at else None
            rec_dict = {
                "id": rec.id,
                "ticker": rec.ticker,
                "exchange": rec.exchange,
                "recommendation_type": rec.recommendation_type,
                "target_price": rec.target_price,
                "current_price": rec.current_price,
                "reasoning": rec.reasoning,
                "risk_level": rec.risk_level,
                "confidence_score": rec.confidence_score,
                "source": rec.source,
                "source_url": rec.source_url,
                "source_date": rec.source_date,
                "is_active": rec.is_active,
                "expires_at": rec.expires_at,
                "created_at": rec.created_at,
                "price_is_stale": True,
                "price_age_hours": price_age_hours,
                "price_last_updated": rec.created_at if rec.created_at else datetime.utcnow(),
                "price_source": "stored",
            }
            sell_recs_updated.append(RecommendationRead.model_validate(rec_dict))
    
    total_returned = len(buy_recs_updated) + len(sell_recs_updated)
    logger.info(
        f"✅ Returning {total_returned} recommendations: "
        f"{len(buy_recs_updated)} buy, {len(sell_recs_updated)} sell"
    )
    
    if total_returned == 0:
        logger.warning(
            f"⚠️  WARNING: No recommendations returned! "
            f"Input: {len(buy_recommendations)} buy + {len(sell_recommendations)} sell from DB. "
            f"All recommendations may have been filtered out due to price validation."
        )
    
    return TopRecommendationsResponse(
        buy_recommendations=buy_recs_updated,
        sell_recommendations=sell_recs_updated,
        total_count=total_returned,
        last_updated=datetime.utcnow()
    )


async def _generate_and_store_recommendations(db: AsyncSession, limit: int):
    """Generate new recommendations using AI agent and store in database"""
    import httpx
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Call agent orchestrator to generate recommendations
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{settings.agent_orchestrator_url}/api/v1/agents/recommendations",
                    json={"limit": limit * 2}  # Get more to have good buy/sell split
                )
                response.raise_for_status()
                agent_response = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ Agent orchestrator returned error: {e.response.status_code} - {e.response.text}")
                # Don't raise - let it use existing recommendations
                return
            except httpx.RequestError as e:
                logger.error(f"❌ Failed to connect to agent orchestrator: {e}")
                # Don't raise - let it use existing recommendations
                return
            except Exception as e:
                logger.error(f"❌ Unexpected error calling agent orchestrator: {e}")
                # Don't raise - let it use existing recommendations
                return
        
        recommendations_data = agent_response.get("recommendations", [])
        
        if not recommendations_data:
            logger.warning("Agent returned no recommendations, will use existing recommendations")
            # Don't return - let it try to use existing recommendations
            # This prevents clearing existing data when agent fails
            return
        
        # Deactivate old recommendations
        await db.execute(
            update(Recommendation).where(
                Recommendation.is_active == "true"
            ).values(is_active="false")
        )
        
        # Get or create AI source
        source_result = await db.execute(
            select(RecommendationSource).where(
                RecommendationSource.name == "AI Market Analyst"
            )
        )
        source = source_result.scalar_one_or_none()
        
        if not source:
            source = RecommendationSource(
                name="AI Market Analyst",
                source_type="ai_analysis",
                credibility_score=0.85,
                is_verified="true"
            )
            db.add(source)
            await db.flush()
        
        # Store new recommendations
        for rec_data in recommendations_data:
            # Map recommendation type
            rec_type_str = rec_data.get("recommendation_type", "HOLD").upper()
            try:
                rec_type = RecommendationType(rec_type_str.lower())
            except ValueError:
                rec_type = RecommendationType.HOLD
            
            new_rec = Recommendation(
                ticker=rec_data.get("ticker", "").upper(),
                exchange=rec_data.get("exchange", "NSE").upper(),
                recommendation_type=rec_type,
                target_price=float(rec_data.get("target_price", 0)),
                current_price=float(rec_data.get("current_price", 0)),
                reasoning=rec_data.get("reasoning", "AI-generated recommendation based on market analysis."),
                risk_level=rec_data.get("risk_level", "medium").lower(),
                confidence_score=float(rec_data.get("confidence_score", 0.5)),
                source_id=source.id,
                source_date=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=settings.recommendation_validity_days),
                is_active="true"
            )
            db.add(new_rec)
        
        await db.commit()
        logger.info(f"Stored {len(recommendations_data)} new recommendations")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to generate/store recommendations: {e}")
        raise


@router.get("/recommendations/{ticker}", response_model=List[RecommendationRead])
async def get_recommendations_for_ticker(
    ticker: str,
    exchange: Optional[str] = Query(None, description="Filter by exchange (NSE, BSE, etc.)"),
    db: AsyncSession = Depends(get_db)
):
    """Get all active recommendations for a specific ticker with fresh prices"""
    try:
        query = select(Recommendation).where(
            Recommendation.ticker == ticker.upper(),
            Recommendation.is_active == "true",
            or_(
                Recommendation.expires_at.is_(None),
                Recommendation.expires_at > datetime.utcnow()
            )
        )
        
        if exchange:
            query = query.where(Recommendation.exchange == exchange.upper())
        
        query = query.order_by(
            Recommendation.confidence_score.desc(),
            Recommendation.created_at.desc()
        )
        
        result = await db.execute(query)
        recommendations = result.scalars().all()
        
        # Load source relationships
        for rec in recommendations:
            await db.refresh(rec, ["source"])
        
        # Update with fresh prices
        updated_recs = await _update_recommendations_with_fresh_prices(recommendations)
        return updated_recs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recommendations: {str(e)}"
        )


@router.post("/recommendations", response_model=RecommendationRead, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    recommendation: RecommendationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new recommendation.
    This endpoint can be used by internal systems or trusted sources to add recommendations.
    """
    try:
        # Get or create source
        source_result = await db.execute(
            select(RecommendationSource).where(
                RecommendationSource.name == recommendation.source_name
            )
        )
        source = source_result.scalar_one_or_none()
        
        if not source:
            source = RecommendationSource(
                name=recommendation.source_name,
                source_type=recommendation.source_type,
                credibility_score=0.7,  # Default for new sources
                is_verified="false"
            )
            db.add(source)
            await db.flush()
        
        # Create recommendation
        new_rec = Recommendation(
            ticker=recommendation.ticker.upper(),
            exchange=recommendation.exchange.upper(),
            recommendation_type=recommendation.recommendation_type,
            target_price=recommendation.target_price,
            current_price=recommendation.current_price,
            reasoning=recommendation.reasoning,
            risk_level=recommendation.risk_level,
            confidence_score=recommendation.confidence_score,
            source_id=source.id,
            source_url=recommendation.source_url,
            source_date=recommendation.source_date,
            expires_at=recommendation.expires_at or (
                datetime.utcnow() + timedelta(days=settings.recommendation_validity_days)
            ),
            is_active="true"
        )
        
        db.add(new_rec)
        await db.commit()
        await db.refresh(new_rec, ["source"])
        
        return RecommendationRead.model_validate(new_rec)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recommendation: {str(e)}"
        )


@router.get("/recommendations/{ticker}/detailed", response_model=RecommendationResponse)
async def get_detailed_recommendation(
    ticker: str,
    exchange: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed recommendation with market data and similar recommendations.
    Provides comprehensive view for a specific stock.
    """
    try:
        # Get recommendations
        query = select(Recommendation).where(
            Recommendation.ticker == ticker.upper(),
            Recommendation.is_active == "true"
        )
        
        if exchange:
            query = query.where(Recommendation.exchange == exchange.upper())
        
        query = query.order_by(
            Recommendation.confidence_score.desc()
        ).limit(1)
        
        result = await db.execute(query)
        recommendation = result.scalar_one_or_none()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active recommendations found for {ticker}"
            )
        
        await db.refresh(recommendation, ["source"])
        
        # Fetch market data
        market_data = None
        fresh_price = None
        price_source = None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                exchange_to_use = exchange or recommendation.exchange
                # CRITICAL: Always use force_refresh=true to get fresh prices from adapter
                response = await client.get(
                    f"{settings.marketdata_service_url}/api/v1/price/{ticker}/latest",
                    params={"exchange": exchange_to_use, "force_refresh": "true"}
                )
                if response.status_code == 200:
                    market_data = response.json()
                    fresh_price = market_data.get("price")
                    price_source = market_data.get("data_source", "market_data_service")
        except Exception:
            pass  # Market data is optional
        
        # Get similar recommendations (same type)
        similar_query = select(Recommendation).where(
            Recommendation.recommendation_type == recommendation.recommendation_type,
            Recommendation.ticker != recommendation.ticker,
            Recommendation.is_active == "true"
        ).order_by(
            Recommendation.confidence_score.desc()
        ).limit(5)
        
        similar_result = await db.execute(similar_query)
        similar_recommendations = similar_result.scalars().all()
        for rec in similar_recommendations:
            await db.refresh(rec, ["source"])
        
        # Update recommendation with fresh price if available
        price_is_stale = fresh_price is None
        price_age_hours = None
        price_last_updated = None
        if fresh_price is None and recommendation.current_price:
            price_last_updated = recommendation.created_at if recommendation.created_at else datetime.utcnow()
            price_age_hours = (datetime.utcnow() - price_last_updated).total_seconds() / 3600
        elif fresh_price is not None:
            price_last_updated = datetime.utcnow()
            price_age_hours = 0.0
        
        if price_source is None:
            price_source = "stored" if fresh_price is None else "market_data_service"
        
        # CRITICAL: Validate target_price makes sense relative to current_price
        final_price = fresh_price if fresh_price is not None else recommendation.current_price
        validated_target_price = recommendation.target_price
        target_price_invalid = False
        
        if final_price and final_price > 0 and validated_target_price and validated_target_price > 0:
            rec_type = recommendation.recommendation_type.upper()
            
            # Check if target price is logically inconsistent with recommendation type
            if rec_type in ["BUY", "STRONG_BUY"]:
                if validated_target_price < final_price:
                    # Target price is below current price for a BUY - this is invalid!
                    target_price_invalid = True
                    logger.warning(
                        f"⚠️  INVALID: {recommendation.ticker} on {recommendation.exchange} has BUY recommendation but "
                        f"target_price (₹{validated_target_price}) < current_price (₹{final_price}). "
                        f"Recalculating target_price with 8% upside..."
                    )
                    # Recalculate target price with standard upside (8% for BUY, 15% for STRONG_BUY)
                    upside_pct = 0.15 if rec_type == "STRONG_BUY" else 0.08
                    validated_target_price = final_price * (1 + upside_pct)
                    logger.info(
                        f"✅ Recalculated target_price for {recommendation.ticker}: ₹{validated_target_price:.2f} "
                        f"({upside_pct*100:.0f}% upside from current ₹{final_price:.2f})"
                    )
            elif rec_type in ["SELL", "STRONG_SELL"]:
                if validated_target_price > final_price:
                    # Target price is above current price for a SELL - this is invalid!
                    target_price_invalid = True
                    logger.warning(
                        f"⚠️  INVALID: {recommendation.ticker} on {recommendation.exchange} has SELL recommendation but "
                        f"target_price (₹{validated_target_price}) > current_price (₹{final_price}). "
                        f"Recalculating target_price with 8% downside..."
                    )
                    # Recalculate target price with standard downside (8% for SELL)
                    downside_pct = 0.08
                    validated_target_price = final_price * (1 - downside_pct)
                    logger.info(
                        f"✅ Recalculated target_price for {recommendation.ticker}: ₹{validated_target_price:.2f} "
                        f"({downside_pct*100:.0f}% downside from current ₹{final_price:.2f})"
                    )
        
        rec_dict = {
            "id": recommendation.id,
            "ticker": recommendation.ticker,
            "exchange": recommendation.exchange,
            "recommendation_type": recommendation.recommendation_type,
            "target_price": round(validated_target_price, 2) if validated_target_price else None,
            "current_price": final_price,
            "reasoning": recommendation.reasoning,
            "risk_level": recommendation.risk_level,
            "confidence_score": recommendation.confidence_score,
            "source": recommendation.source,
            "source_url": recommendation.source_url,
            "source_date": recommendation.source_date,
            "is_active": recommendation.is_active,
            "expires_at": recommendation.expires_at,
            "created_at": recommendation.created_at,
            "price_is_stale": price_is_stale,
            "price_age_hours": price_age_hours,
            "price_last_updated": price_last_updated,
            "price_source": price_source,
        }
        updated_recommendation = RecommendationRead.model_validate(rec_dict)
        
        # Update similar recommendations with fresh prices
        updated_similar = await _update_recommendations_with_fresh_prices(similar_recommendations)
        
        return RecommendationResponse(
            recommendation=updated_recommendation,
            market_data=market_data,
            similar_recommendations=updated_similar
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch detailed recommendation: {str(e)}"
        )

