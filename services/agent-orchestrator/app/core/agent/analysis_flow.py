"""Analysis Flow agent"""
import json
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.agent.agent_base import BaseAgentFlow
from app.models.agent import AgentRun
from app.schemas.agent import Metric, SourceCitation

logger = logging.getLogger(__name__)


class AnalysisFlow(BaseAgentFlow):
    """Agent flow for portfolio analysis"""
    
    async def execute(self, portfolio_id: int, user_id: int) -> Dict[str, Any]:
        """Execute analysis flow"""
        await self._initialize()
        
        try:
            # Step 1: Fetch consolidated holdings
            holdings_result = await self.aggregator_tool.get_consolidated_holdings(user_id)
            await self._log_action(
                "aggregator.get_consolidated_holdings",
                {"user_id": user_id},
                holdings_result
            )
            
            holdings_data = holdings_result["data"]
            holdings = holdings_data.get("holdings", [])
            
            if not holdings:
                await self._update_run_status("completed", {
                    "explanation": "No holdings found for analysis",
                    "metrics": [],
                    "sources": []
                })
                return self.agent_run.output_json
            
            # Step 2: Get current prices for all instruments
            price_data = {}
            for holding in holdings:
                ticker = holding.get("ticker")
                exchange = holding.get("exchange")
                if ticker and exchange:
                    try:
                        price_result = await self.marketdata_tool.get_latest_price(ticker, exchange)
                        await self._log_action(
                            "marketdata.get_latest_price",
                            {"ticker": ticker, "exchange": exchange},
                            price_result
                        )
                        price_data[f"{ticker}:{exchange}"] = price_result["data"]
                    except Exception as e:
                        logger.warning(f"Failed to get price for {ticker}: {e}")
            
            # Step 3: Compute portfolio metrics
            metrics_result = await self.analytics_tool.compute_portfolio_metrics(holdings)
            await self._log_action(
                "analytics.compute_portfolio_metrics",
                {"holdings_count": len(holdings)},
                metrics_result
            )
            
            metrics_data = metrics_result["data"]
            
            # Step 4: Build structured metrics with citations
            structured_metrics: List[Metric] = []
            
            if "total_valuation" in metrics_data:
                structured_metrics.append(Metric(
                    name="Total Portfolio Value",
                    value=float(metrics_data["total_valuation"]),
                    unit="INR",
                    source=self.analytics_tool._create_citation("/api/v1/portfolio/metrics", "total_valuation")
                ))
            
            if "holdings_count" in metrics_data:
                structured_metrics.append(Metric(
                    name="Number of Holdings",
                    value=float(metrics_data["holdings_count"]),
                    source=self.analytics_tool._create_citation("/api/v1/portfolio/metrics", "holdings_count")
                ))
            
            # Add individual holding metrics
            for holding in holdings:
                ticker = holding.get("ticker", "Unknown")
                total_qty = holding.get("total_qty", 0)
                total_valuation = holding.get("total_valuation", 0)
                
                structured_metrics.append(Metric(
                    name=f"{ticker} Quantity",
                    value=float(total_qty),
                    source=self.aggregator_tool._create_citation(f"/api/v1/holdings/{user_id}", f"{ticker}_quantity")
                ))
                
                if total_valuation:
                    structured_metrics.append(Metric(
                        name=f"{ticker} Valuation",
                        value=float(total_valuation),
                        unit="INR",
                        source=self.aggregator_tool._create_citation(f"/api/v1/holdings/{user_id}", f"{ticker}_valuation")
                    ))
            
            # Step 5: Generate explanation
            explanation = self._generate_explanation(holdings, metrics_data, price_data)
            
            # Step 6: Store in vector store for future reference
            context_text = f"Portfolio analysis for user {user_id}: {explanation}"
            await self.vector_store.store(
                context_text,
                {
                    "user_id": user_id,
                    "portfolio_id": portfolio_id,
                    "flow_type": "analysis",
                    "agent_run_id": self.agent_run.id
                }
            )
            
            # Step 7: Build response
            output = {
                "explanation": explanation,
                "metrics": [m.dict() for m in structured_metrics],
                "sources": [s.dict() for s in self.sources],
                "status": "completed"
            }
            
            await self._update_run_status("completed", output)
            return output
            
        except Exception as e:
            logger.error(f"Analysis flow error: {e}")
            await self._update_run_status("failed", {"error": str(e)})
            raise
    
    def _generate_explanation(
        self,
        holdings: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        price_data: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation"""
        total_value = metrics.get("total_valuation", 0)
        holdings_count = len(holdings)
        
        explanation = f"Portfolio Analysis Summary:\n\n"
        explanation += f"Total Portfolio Value: ₹{total_value:,.2f}\n"
        explanation += f"Number of Holdings: {holdings_count}\n\n"
        
        explanation += "Top Holdings:\n"
        sorted_holdings = sorted(holdings, key=lambda x: x.get("total_valuation", 0), reverse=True)[:5]
        for i, holding in enumerate(sorted_holdings, 1):
            ticker = holding.get("ticker", "Unknown")
            qty = holding.get("total_qty", 0)
            val = holding.get("total_valuation", 0)
            explanation += f"{i}. {ticker}: {qty} shares, Value: ₹{val:,.2f}\n"
        
        explanation += "\nAnalysis completed using data from aggregator, marketdata, and analytics services."
        return explanation

