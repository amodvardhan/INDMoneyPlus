"""News API endpoints for stock-related news"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class NewsArticle:
    """News article model"""
    def __init__(self, title: str, url: str, source: str, published_at: datetime, snippet: Optional[str] = None):
        self.title = title
        self.url = url
        self.source = source
        self.published_at = published_at
        self.snippet = snippet


async def fetch_news_from_yahoo(ticker: str, exchange: str, limit: int = 10) -> List[dict]:
    """
    Fetch news articles for a stock from Yahoo Finance
    Returns a list of news articles
    """
    try:
        # Convert ticker to Yahoo Finance symbol
        exchange_map = {
            "NSE": ".NS",
            "BSE": ".BO",
            "NASDAQ": "",
            "NYSE": "",
        }
        suffix = exchange_map.get(exchange.upper(), "")
        symbol = f"{ticker.upper()}{suffix}"
        
        logger.info(f"🔍 Fetching news for symbol: {symbol} (ticker: {ticker}, exchange: {exchange})")
        
        # PRIORITY: Try yfinance library first (most reliable)
        try:
            import yfinance as yf
            import asyncio
            
            logger.info(f"🔄 Using yfinance library for {symbol} (primary method)")
            loop = asyncio.get_event_loop()
            
            # Run yfinance in executor (it's synchronous)
            logger.info(f"📦 Creating yfinance Ticker object for {symbol}")
            ticker_obj = await loop.run_in_executor(None, yf.Ticker, symbol)
            
            logger.info(f"📰 Fetching news from yfinance for {symbol}")
            news_data = await loop.run_in_executor(None, lambda: ticker_obj.news)
            
            logger.info(f"📊 yfinance news response: type={type(news_data)}, length={len(news_data) if news_data else 0}")
            
            if news_data and len(news_data) > 0:
                logger.info(f"✅ yfinance returned {len(news_data)} news items")
                # Log first item structure at INFO level for debugging
                first_item = news_data[0]
                logger.info(f"📋 First news item keys: {list(first_item.keys()) if isinstance(first_item, dict) else 'Not a dict'}")
                logger.info(f"📋 First news item sample: title={first_item.get('title', 'N/A')[:50] if isinstance(first_item, dict) else 'N/A'}, link={first_item.get('link', 'N/A')[:50] if isinstance(first_item, dict) else 'N/A'}")
                
                articles = []
                for idx, item in enumerate(news_data[:limit * 2]):  # Check more items to find valid ones
                    try:
                        # yfinance news structure: title, link, publisher, providerPublishTime, type, uuid
                        # Log item structure for first few items
                        if idx < 3:
                            logger.info(f"🔍 Processing item {idx}: type={type(item)}, keys={list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
                        
                        if not isinstance(item, dict):
                            logger.warning(f"⚠️ Item {idx} is not a dictionary: {type(item)}")
                            continue
                        
                        title = item.get("title") or item.get("headline") or ""
                        url = item.get("link") or item.get("url") or ""
                        summary = item.get("summary") or item.get("description") or ""
                        publisher = item.get("publisher") or item.get("provider") or "Yahoo Finance"
                        
                        # Log what we found
                        if idx < 3:
                            logger.info(f"📝 Item {idx} extracted: title={title[:50] if title else 'EMPTY'}, url={url[:50] if url else 'EMPTY'}, publisher={publisher}")
                        
                        # Skip if essential fields are missing or empty
                        if not title or not title.strip() or not url or not url.strip():
                            logger.warning(f"⚠️ Skipping item {idx}: title={bool(title and title.strip())}, url={bool(url and url.strip())}")
                            continue
                        
                        published_time = item.get("providerPublishTime")
                        if published_time:
                            try:
                                if isinstance(published_time, (int, float)):
                                    published_at = datetime.fromtimestamp(published_time)
                                else:
                                    published_at = datetime.fromisoformat(str(published_time).replace('Z', '+00:00'))
                            except (ValueError, OSError, TypeError) as e:
                                logger.debug(f"Error parsing yfinance timestamp: {e}")
                                published_at = datetime.utcnow()
                        else:
                            published_at = datetime.utcnow()
                        
                        # Clean and truncate snippet
                        snippet = summary.strip()[:200] if summary and summary.strip() else None
                        
                        articles.append({
                            "title": title.strip(),
                            "url": url.strip(),
                            "source": publisher,
                            "published_at": published_at,
                            "snippet": snippet
                        })
                        
                        # Stop when we have enough valid articles
                        if len(articles) >= limit:
                            break
                            
                    except Exception as e:
                        logger.error(f"❌ Error parsing yfinance news item {idx}: {e}", exc_info=True)
                        continue
                
                if articles:
                    logger.info(f"✅ Successfully parsed {len(articles)} news articles from yfinance")
                    return articles
                else:
                    logger.warning(f"⚠️ No valid articles found after parsing {len(news_data)} yfinance items")
            else:
                logger.warning(f"⚠️ yfinance returned no news items for {symbol}")
        except ImportError as e:
            logger.error(f"❌ yfinance library not available: {e}. Install with: poetry add yfinance")
        except Exception as e:
            logger.error(f"❌ yfinance failed: {e}", exc_info=True)
        
        # Fallback: Try Yahoo Finance search API with proper headers
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search"
            params = {
                "q": symbol,
                "quotes_count": 1,
                "news_count": limit * 2,
                "enableFuzzyQuery": False
            }
            
            # Add headers to mimic browser request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://finance.yahoo.com/",
            }
            
            client = get_http_client()
            logger.info(f"🌐 Calling Yahoo Finance search API: {url} with params {params}")
            response = await client.get(url, params=params, headers=headers, timeout=15.0)
            logger.info(f"📡 Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Yahoo Finance search API returned {response.status_code} for {symbol}")
            else:
                data = response.json()
                news_items = data.get("news", [])
                logger.info(f"📰 Yahoo Finance search API returned {len(news_items)} news items for {symbol}")
                
                # Log full response structure for debugging
                if news_items:
                    logger.debug(f"Sample news item keys: {list(news_items[0].keys()) if news_items else 'No items'}")
                    logger.debug(f"Sample news item: {news_items[0] if news_items else 'No items'}")
                else:
                    logger.debug(f"Full API response structure: {list(data.keys())}")
                    logger.debug(f"Full API response: {data}")
                
                if news_items:
                    articles = []
                    for item in news_items[:limit * 2]:  # Check more items to find valid ones
                        try:
                            # Extract fields with multiple possible keys
                            title = item.get("title") or item.get("headline") or item.get("name") or ""
                            url = item.get("link") or item.get("url") or item.get("uuid") or ""
                            summary = item.get("summary") or item.get("description") or item.get("text") or ""
                            publisher = item.get("publisher") or item.get("source") or "Yahoo Finance"
                            
                            # Skip if essential fields are missing or empty
                            if not title or not title.strip() or not url or not url.strip():
                                logger.debug(f"Skipping item with missing title/url: title={bool(title)}, url={bool(url)}")
                                continue
                                
                            published_time = item.get("providerPublishTime") or item.get("publishTime") or item.get("time")
                            if published_time:
                                try:
                                    # Handle both timestamp (int/float) and ISO string
                                    if isinstance(published_time, (int, float)):
                                        published_at = datetime.fromtimestamp(published_time)
                                    else:
                                        published_at = datetime.fromisoformat(str(published_time).replace('Z', '+00:00'))
                                except (ValueError, OSError, TypeError) as e:
                                    logger.debug(f"Error parsing timestamp {published_time}: {e}")
                                    published_at = datetime.utcnow()
                            else:
                                published_at = datetime.utcnow()
                            
                            # Clean and truncate snippet
                            snippet = summary.strip()[:200] if summary and summary.strip() else None
                            
                            articles.append({
                                "title": title.strip(),
                                "url": url.strip(),
                                "source": publisher,
                                "published_at": published_at,
                                "snippet": snippet
                            })
                            
                            # Stop when we have enough valid articles
                            if len(articles) >= limit:
                                break
                                
                        except Exception as e:
                            logger.debug(f"Error parsing news item: {e}", exc_info=True)
                            continue
                    
                    if articles:
                        logger.info(f"✅ Successfully parsed {len(articles)} news articles from search API")
                        return articles
                else:
                    logger.warning(f"⚠️ No valid articles found after parsing {len(news_items)} items")
        except Exception as e:
            logger.warning(f"⚠️ Yahoo Finance search API failed: {e}", exc_info=True)
        
        logger.warning(f"❌ No news articles found for {symbol} using any method")
        return []
        
    except Exception as e:
        logger.error(f"❌ Error fetching news from Yahoo Finance for {ticker}: {e}", exc_info=True)
        return []


# Global HTTP client for news fetching
_news_http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    """Get shared HTTP client for news fetching"""
    global _news_http_client
    if _news_http_client is None:
        _news_http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
            follow_redirects=True
        )
    return _news_http_client


@router.get("/news/{ticker}")
async def get_stock_news(
    ticker: str,
    exchange: str = Query("NSE", description="Exchange code (e.g., NSE, NASDAQ)"),
    limit: int = Query(10, ge=1, le=50, description="Number of news articles to return")
):
    """
    Get recent news articles for a stock ticker
    Fetches news from Yahoo Finance and other sources
    """
    logger.info(f"📰 News API called: ticker={ticker}, exchange={exchange}, limit={limit}")
    try:
        articles = await fetch_news_from_yahoo(ticker, exchange, limit)
        
        # Filter out any articles with empty titles or URLs (safety check)
        valid_articles = [
            article for article in articles
            if article.get("title") and article.get("title", "").strip() 
            and article.get("url") and article.get("url", "").strip()
        ]
        
        # If no valid articles found, return empty list (don't fail)
        if not valid_articles:
            logger.warning(f"⚠️ No valid news articles found for {ticker} on {exchange} (received {len(articles)} articles, but all were invalid)")
            return {
                "ticker": ticker,
                "exchange": exchange,
                "articles": [],
                "count": 0
            }
        
        logger.info(f"✅ Successfully fetched {len(valid_articles)} valid news articles for {ticker} (filtered from {len(articles)} total)")
        return {
            "ticker": ticker,
            "exchange": exchange,
            "articles": valid_articles,
            "count": len(valid_articles)
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching news for {ticker}: {e}", exc_info=True)
        # Return empty result instead of failing
        return {
            "ticker": ticker,
            "exchange": exchange,
            "articles": [],
            "count": 0,
            "error": str(e)
        }
