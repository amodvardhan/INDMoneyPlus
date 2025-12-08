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
        
        # Yahoo Finance news endpoint
        url = f"https://query1.finance.yahoo.com/v1/finance/search"
        params = {
            "q": symbol,
            "quotes_count": 1,
            "news_count": limit,
            "enableFuzzyQuery": False
        }
        
        client = get_http_client()
        response = await client.get(url, params=params, timeout=10.0)
        
        if response.status_code != 200:
            logger.warning(f"Yahoo Finance news API returned {response.status_code} for {ticker}")
            return []
        
        data = response.json()
        news_items = data.get("news", [])
        
        articles = []
        for item in news_items[:limit]:
            try:
                articles.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "source": item.get("publisher", "Unknown"),
                    "published_at": datetime.fromtimestamp(item.get("providerPublishTime", 0)) if item.get("providerPublishTime") else datetime.utcnow(),
                    "snippet": item.get("summary", "")[:200] if item.get("summary") else None
                })
            except Exception as e:
                logger.debug(f"Error parsing news item: {e}")
                continue
        
        logger.info(f"Fetched {len(articles)} news articles for {ticker} on {exchange}")
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching news from Yahoo Finance for {ticker}: {e}", exc_info=True)
        return []


# Global HTTP client for news fetching
_news_http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    """Get shared HTTP client for news fetching"""
    global _news_http_client
    if _news_http_client is None:
        _news_http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50)
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
    try:
        articles = await fetch_news_from_yahoo(ticker, exchange, limit)
        
        # If no articles found, return empty list (don't fail)
        if not articles:
            logger.info(f"No news articles found for {ticker} on {exchange}")
            return {
                "ticker": ticker,
                "exchange": exchange,
                "articles": [],
                "count": 0
            }
        
        return {
            "ticker": ticker,
            "exchange": exchange,
            "articles": articles,
            "count": len(articles)
        }
        
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}", exc_info=True)
        # Return empty result instead of failing
        return {
            "ticker": ticker,
            "exchange": exchange,
            "articles": [],
            "count": 0,
            "error": "Failed to fetch news"
        }
