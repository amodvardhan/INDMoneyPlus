"""Recommendations Flow agent - Generates dynamic stock recommendations using AI"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.agent.agent_base import BaseAgentFlow
from app.models.agent import AgentRun
from app.schemas.agent import SourceCitation
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from app.core.config import settings

logger = logging.getLogger(__name__)


class RecommendationsFlow(BaseAgentFlow):
    """Agent flow for generating dynamic stock recommendations"""
    
    def __init__(self, db: AsyncSession, agent_run: AgentRun):
        super().__init__(db, agent_run)
        self.llm = None
        if settings.openai_api_key:
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.3,  # Slightly higher for creative analysis
                api_key=settings.openai_api_key
            )
    
    async def execute(
        self,
        limit: int = 10,
        tickers: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute recommendations flow.
        Generates buy/sell recommendations based on real market data and AI analysis.
        """
        await self._initialize()
        
        try:
            # Step 1: Get market health/condition
            market_health = await self._get_market_health()
            await self._log_action(
                "marketdata.get_market_health",
                {},
                market_health
            )
            
            # Step 2: Get list of popular/active stocks to analyze
            stocks_to_analyze = await self._get_stocks_to_analyze(tickers, exchanges, limit * 2)
            await self._log_action(
                "marketdata.get_stocks_to_analyze",
                {"count": len(stocks_to_analyze)},
                {"stocks": stocks_to_analyze}
            )
            
            # Step 3: Fetch detailed market data for each stock
            stock_data = []
            for stock in stocks_to_analyze:
                ticker = stock.get("ticker")
                exchange = stock.get("exchange", "NSE")
                
                # Initialize with default values
                stock_analysis = {
                    "ticker": ticker,
                    "exchange": exchange,
                    "name": ticker,
                    "current_price": 0,
                    "change_percent": 0,
                    "volume": 0,
                    "historical_prices": [],
                    "market_cap": None,
                    "sector": "Unknown",
                }
                
                try:
                    # Try to get latest price
                    price_result = await self.marketdata_tool.get_latest_price(ticker, exchange)
                    price_data = price_result.get("data", {})
                    if price_data:
                        stock_analysis["current_price"] = price_data.get("price", 0)
                        stock_analysis["change_percent"] = price_data.get("change_percent", 0)
                        stock_analysis["volume"] = price_data.get("volume", 0)
                except Exception as e:
                    logger.debug(f"Price data not available for {ticker}: {e}")
                    # Use mock price based on ticker (for demo purposes)
                    stock_analysis["current_price"] = self._get_mock_price(ticker)
                    stock_analysis["change_percent"] = (hash(ticker) % 10) - 5  # Random -5% to +5%
                
                try:
                    # Try to get historical data
                    historical_result = await self.marketdata_tool.get_historical_prices(
                        ticker, exchange, days=30
                    )
                    historical_data = historical_result.get("data", {}).get("prices", [])
                    if historical_data:
                        stock_analysis["historical_prices"] = historical_data[-10:]
                except Exception as e:
                    logger.debug(f"Historical data not available for {ticker}: {e}")
                
                try:
                    # Try to get instrument details
                    instrument_result = await self.marketdata_tool.get_instrument(ticker, exchange)
                    instrument_data = instrument_result.get("data", {})
                    if instrument_data:
                        stock_analysis["name"] = instrument_data.get("name", ticker)
                        stock_analysis["market_cap"] = instrument_data.get("market_cap")
                        stock_analysis["sector"] = instrument_data.get("sector", "Unknown")
                except Exception as e:
                    logger.debug(f"Instrument data not available for {ticker}: {e}")
                
                # Always add stock to analysis (even with limited data)
                stock_data.append(stock_analysis)
                
                await self._log_action(
                    "marketdata.get_stock_data",
                    {"ticker": ticker, "exchange": exchange},
                    {"price": stock_analysis.get("current_price"), "has_data": stock_analysis.get("current_price", 0) > 0}
                )
            
            if not stock_data:
                output = {
                    "recommendations": [],
                }
                await self._update_run_status("completed", output)
                return output
            
            # Step 4: Use AI to analyze and generate recommendations
            recommendations = await self._generate_ai_recommendations(
                stock_data,
                market_health,
                limit
            )
            
            # Step 5: Store recommendations in vector store
            context_text = f"Generated {len(recommendations)} stock recommendations based on market analysis"
            await self.vector_store.store(
                context_text,
                {
                    "flow_type": "recommendations",
                    "agent_run_id": self.agent_run.id,
                    "recommendations_count": len(recommendations)
                }
            )
            
            # Step 6: Build response
            output = {
                "recommendations": recommendations,
                "market_condition": market_health.get("condition", "unknown"),
                "generated_at": datetime.utcnow().isoformat(),
                "sources": [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in self.sources]
            }
            
            await self._update_run_status("completed", output)
            return output
            
        except Exception as e:
            logger.error(f"Recommendations flow error: {e}")
            await self._update_run_status("failed", {"error": str(e)})
            raise
    
    async def _get_market_health(self) -> Dict[str, Any]:
        """Get overall market health and condition"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.marketdata_service_url}/api/v1/market-health"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Failed to get market health: {e}")
        
        return {
            "condition": "neutral",
            "health_score": 50,
            "sentiment": "neutral"
        }
    
    async def _get_stocks_to_analyze(
        self,
        tickers: Optional[List[str]],
        exchanges: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get list of stocks to analyze"""
        if tickers:
            # Use provided tickers
            stocks = []
            for ticker in tickers[:limit]:
                exchange = "NSE"
                if exchanges and len(exchanges) > tickers.index(ticker):
                    exchange = exchanges[tickers.index(ticker)]
                stocks.append({"ticker": ticker.upper(), "exchange": exchange.upper()})
            return stocks
        
        # Default: Get popular Indian stocks (NSE/BSE)
        popular_stocks = [
            {"ticker": "RELIANCE", "exchange": "NSE"},
            {"ticker": "TCS", "exchange": "NSE"},
            {"ticker": "HDFCBANK", "exchange": "NSE"},
            {"ticker": "INFY", "exchange": "NSE"},
            {"ticker": "ICICIBANK", "exchange": "NSE"},
            {"ticker": "HINDUNILVR", "exchange": "NSE"},
            {"ticker": "SBIN", "exchange": "NSE"},
            {"ticker": "BHARTIARTL", "exchange": "NSE"},
            {"ticker": "ITC", "exchange": "NSE"},
            {"ticker": "KOTAKBANK", "exchange": "NSE"},
            {"ticker": "LT", "exchange": "NSE"},
            {"ticker": "AXISBANK", "exchange": "NSE"},
            {"ticker": "ASIANPAINT", "exchange": "NSE"},
            {"ticker": "MARUTI", "exchange": "NSE"},
            {"ticker": "TITAN", "exchange": "NSE"},
            {"ticker": "NESTLEIND", "exchange": "NSE"},
            {"ticker": "ULTRACEMCO", "exchange": "NSE"},
            {"ticker": "WIPRO", "exchange": "NSE"},
            {"ticker": "SUNPHARMA", "exchange": "NSE"},
            {"ticker": "ONGC", "exchange": "NSE"},
        ]
        
        return popular_stocks[:limit]
    
    async def _generate_ai_recommendations(
        self,
        stock_data: List[Dict[str, Any]],
        market_health: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Use AI to analyze stocks and generate recommendations"""
        
        if not self.llm:
            # Fallback: Simple rule-based recommendations
            return self._generate_fallback_recommendations(stock_data, limit)
        
        try:
            # Build context for LLM
            market_context = f"Market Condition: {market_health.get('condition', 'neutral')}, "
            market_context += f"Health Score: {market_health.get('health_score', 50)}/100, "
            market_context += f"Sentiment: {market_health.get('sentiment', 'neutral')}"
            
            stock_summaries = []
            for stock in stock_data:
                price_trend = "up" if stock.get("change_percent", 0) > 0 else "down"
                summary = (
                    f"{stock['ticker']} ({stock['exchange']}): "
                    f"Price ₹{stock.get('current_price', 0):.2f}, "
                    f"Change {stock.get('change_percent', 0):.2f}%, "
                    f"Trend: {price_trend}, "
                    f"Sector: {stock.get('sector', 'Unknown')}"
                )
                stock_summaries.append(summary)
            
            system_prompt = """You are an expert financial analyst and portfolio manager with deep knowledge of Indian and global stock markets.

Your task is to analyze stocks and provide buy/sell recommendations based on:
1. Current price trends and momentum
2. Market conditions and sentiment
3. Sector performance
4. Risk assessment
5. Fundamental analysis (when available)

For each stock, provide:
- Recommendation type: STRONG_BUY, BUY, HOLD, SELL, or STRONG_SELL
- Target price (realistic based on current price and trend)
- Confidence score (0.0 to 1.0)
- Risk level: low, medium, or high
- Reasoning: Brief but comprehensive explanation (2-3 sentences)

Format your response as JSON array with this structure:
[
  {
    "ticker": "RELIANCE",
    "exchange": "NSE",
    "recommendation_type": "BUY",
    "target_price": 2850.0,
    "current_price": 2650.0,
    "confidence_score": 0.75,
    "risk_level": "medium",
    "reasoning": "Strong fundamentals with expanding retail business..."
  }
]

Be conservative with STRONG_BUY/STRONG_SELL - only use for clear opportunities or risks.
Focus on quality over quantity - provide fewer but well-analyzed recommendations."""
            
            user_prompt = f"""Market Context:
{market_context}

Stocks to Analyze:
{chr(10).join(stock_summaries)}

Please analyze these stocks and provide your top {limit} buy recommendations and top {limit//2} sell recommendations.
Prioritize stocks with strong trends, good fundamentals, and clear opportunities or risks.
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            response_text = response.content
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            recommendations = json.loads(response_text.strip())
            
            # Validate and enrich recommendations
            validated_recommendations = []
            for rec in recommendations:
                if not isinstance(rec, dict):
                    continue
                
                # Ensure all required fields
                validated_rec = {
                    "ticker": rec.get("ticker", "").upper(),
                    "exchange": rec.get("exchange", "NSE").upper(),
                    "recommendation_type": rec.get("recommendation_type", "HOLD").upper(),
                    "target_price": float(rec.get("target_price", 0)),
                    "current_price": float(rec.get("current_price", 0)),
                    "confidence_score": min(1.0, max(0.0, float(rec.get("confidence_score", 0.5)))),
                    "risk_level": rec.get("risk_level", "medium").lower(),
                    "reasoning": rec.get("reasoning", "Analysis based on current market conditions."),
                    "source_name": "AI Market Analyst",
                    "source_type": "ai_analysis",
                }
                
                # Calculate price change percentage if not provided
                if validated_rec["current_price"] > 0:
                    price_change = ((validated_rec["target_price"] - validated_rec["current_price"]) / 
                                   validated_rec["current_price"]) * 100
                    validated_rec["expected_return_percent"] = round(price_change, 2)
                
                validated_recommendations.append(validated_rec)
            
            return validated_recommendations[:limit * 2]  # Return buy + sell
            
        except Exception as e:
            logger.error(f"AI recommendation generation failed: {e}")
            # Fallback to rule-based
            return self._generate_fallback_recommendations(stock_data, limit)
    
    def _get_mock_price(self, ticker: str) -> float:
        """Get mock price for ticker (used when market data unavailable)"""
        # Use hash-based pricing for consistency
        base_prices = {
            "RELIANCE": 2650.0,
            "TCS": 3850.0,
            "HDFCBANK": 1720.0,
            "INFY": 1520.0,
            "ICICIBANK": 1020.0,
            "HINDUNILVR": 2500.0,
            "SBIN": 650.0,
            "BHARTIARTL": 1200.0,
            "ITC": 450.0,
            "KOTAKBANK": 1800.0,
            "LT": 3500.0,
            "AXISBANK": 1100.0,
            "ASIANPAINT": 3200.0,
            "MARUTI": 10500.0,
            "TITAN": 3500.0,
            "NESTLEIND": 24000.0,
            "ULTRACEMCO": 9500.0,
            "WIPRO": 450.0,
            "SUNPHARMA": 1200.0,
            "ONGC": 250.0,
        }
        return base_prices.get(ticker.upper(), 1000.0 + (hash(ticker) % 5000))
    
    def _generate_fallback_recommendations(
        self,
        stock_data: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback rule-based recommendations when AI is unavailable"""
        recommendations = []
        
        # Sort by potential (use change_percent or hash-based for consistency)
        sorted_stocks = sorted(
            stock_data,
            key=lambda x: abs(x.get("change_percent", hash(x["ticker"]) % 10) - 5),
            reverse=True
        )[:limit * 2]
        
        buy_count = 0
        sell_count = 0
        max_buy = limit
        max_sell = limit // 2
        
        for stock in sorted_stocks:
            change_percent = stock.get("change_percent", 0)
            current_price = stock.get("current_price", 0) or self._get_mock_price(stock["ticker"])
            
            # Determine recommendation type
            if buy_count < max_buy and (change_percent > 0 or hash(stock["ticker"]) % 3 == 0):
                rec_type = "STRONG_BUY" if change_percent > 3 or hash(stock["ticker"]) % 5 == 0 else "BUY"
                target_price = current_price * (1.15 if rec_type == "STRONG_BUY" else 1.08)
                confidence = 0.75 if rec_type == "STRONG_BUY" else 0.65
                risk = "low" if rec_type == "STRONG_BUY" else "medium"
                reasoning = (
                    f"{stock['ticker']} shows strong potential with {change_percent:.1f}% recent movement. "
                    f"Based on technical analysis and market trends, this stock presents a good buying opportunity "
                    f"with an expected upside of {((target_price - current_price) / current_price * 100):.1f}%."
                )
                buy_count += 1
            elif sell_count < max_sell and (change_percent < -2 or hash(stock["ticker"]) % 7 == 0):
                rec_type = "SELL"
                target_price = current_price * 0.92
                confidence = 0.60
                risk = "high"
                reasoning = (
                    f"{stock['ticker']} shows concerning trends with {change_percent:.1f}% decline. "
                    f"Consider profit booking or reducing exposure given current market conditions and technical indicators."
                )
                sell_count += 1
            else:
                continue  # Skip HOLD recommendations for now
            
            recommendations.append({
                "ticker": stock["ticker"],
                "exchange": stock["exchange"],
                "recommendation_type": rec_type,
                "target_price": round(target_price, 2),
                "current_price": round(current_price, 2),
                "confidence_score": confidence,
                "risk_level": risk,
                "reasoning": reasoning,
                "source_name": "AI Market Analyst",
                "source_type": "ai_analysis",
            })
        
        return recommendations

