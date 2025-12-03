"""WebSocket endpoint for streaming price updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import json
import logging
import asyncio
from app.core.adapters import MarketDataAdapter, InMemoryAdapter

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()

_adapter: MarketDataAdapter = None


def get_adapter() -> MarketDataAdapter:
    """Get market data adapter"""
    global _adapter
    if _adapter is None:
        _adapter = InMemoryAdapter()
    return _adapter


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket endpoint for streaming price updates from market data adapter"""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket connection established. Total connections: {len(active_connections)}")
    
    subscribed_tickers = set()
    adapter = get_adapter()
    
    try:
        while True:
            # Wait for client message with timeout
            try:
                # Use asyncio.wait_for to handle both receive and timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                message = json.loads(data)
                
                if message.get("type") == "subscribe":
                    ticker = message.get("ticker")
                    exchange = message.get("exchange", "NSE")
                    if ticker:
                        subscribed_tickers.add((ticker.upper(), exchange.upper()))
                        await websocket.send_json({
                            "type": "subscribed",
                            "ticker": ticker,
                            "exchange": exchange
                        })
                
                elif message.get("type") == "unsubscribe":
                    ticker = message.get("ticker")
                    exchange = message.get("exchange", "NSE")
                    if ticker:
                        subscribed_tickers.discard((ticker.upper(), exchange.upper()))
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "ticker": ticker,
                            "exchange": exchange
                        })
                
            except asyncio.TimeoutError:
                # Timeout is expected - continue to send price updates
                pass
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            
            # Send price updates for subscribed tickers
            for ticker, exchange in subscribed_tickers:
                try:
                    latest_price = await adapter.get_latest_price(ticker, exchange)
                    if latest_price:
                        await websocket.send_json({
                            "type": "price_update",
                            "ticker": latest_price.ticker,
                            "exchange": latest_price.exchange,
                            "price": latest_price.price,
                            "timestamp": latest_price.timestamp.isoformat(),
                            "open": latest_price.open,
                            "high": latest_price.high,
                            "low": latest_price.low,
                            "close": latest_price.close,
                            "volume": latest_price.volume
                        })
                except Exception as e:
                    logger.error(f"Error fetching price for {ticker} on {exchange}: {e}")
            
            # Small delay to avoid overwhelming the client
            await asyncio.sleep(1.0)
            
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        active_connections.discard(websocket)
        try:
            await websocket.close()
        except:
            pass

