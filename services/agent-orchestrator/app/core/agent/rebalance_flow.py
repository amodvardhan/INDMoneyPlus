"""Rebalance Flow agent"""
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.agent.agent_base import BaseAgentFlow
from app.models.agent import AgentRun
from app.schemas.agent import TradeProposal, SourceCitation

logger = logging.getLogger(__name__)


class RebalanceFlow(BaseAgentFlow):
    """Agent flow for rebalancing proposal generation"""
    
    async def execute(
        self,
        portfolio_id: int,
        user_id: int,
        target_alloc: Dict[str, float]
    ) -> Dict[str, Any]:
        """Execute rebalance flow"""
        await self._initialize()
        
        try:
            # Step 1: Fetch current holdings
            holdings_result = await self.aggregator_tool.get_consolidated_holdings(user_id)
            await self._log_action(
                "aggregator.get_consolidated_holdings",
                {"user_id": user_id},
                holdings_result
            )
            
            holdings_data = holdings_result["data"]
            current_holdings = holdings_data.get("holdings", [])
            total_value = holdings_data.get("total_valuation", 0)
            
            if not current_holdings:
                output = {
                    "proposal": [],
                    "total_estimated_cost": 0.0,
                    "total_estimated_tax": None,
                    "explanation": "No holdings to rebalance",
                    "sources": [],
                    "status": "completed"
                }
                await self._update_run_status("completed", output)
                return output
            
            # Step 2: Run rebalance simulation
            rebalance_result = await self.analytics_tool.simulate_rebalance(
                current_holdings=current_holdings,
                target_allocation=target_alloc
            )
            await self._log_action(
                "analytics.simulate_rebalance",
                {"target_allocation": target_alloc},
                rebalance_result
            )
            
            rebalance_data = rebalance_result["data"]
            trade_proposals_data = rebalance_data.get("trades", [])
            
            # Step 3: Get current prices and build trade proposals
            trade_proposals: List[TradeProposal] = []
            total_cost = 0.0
            total_tax = 0.0
            
            for trade_data in trade_proposals_data:
                ticker = trade_data.get("ticker")
                exchange = trade_data.get("exchange", "NSE")
                action = trade_data.get("action", "BUY")
                quantity = trade_data.get("quantity", 0)
                
                # Get current price
                try:
                    price_result = await self.marketdata_tool.get_latest_price(ticker, exchange)
                    await self._log_action(
                        "marketdata.get_latest_price",
                        {"ticker": ticker, "exchange": exchange},
                        price_result
                    )
                    current_price = price_result["data"].get("price", 0)
                except Exception as e:
                    logger.warning(f"Failed to get price for {ticker}: {e}")
                    current_price = trade_data.get("estimated_price", 0)
                
                estimated_cost = abs(quantity * current_price)
                estimated_tax = trade_data.get("estimated_tax", 0)
                
                if action == "BUY":
                    total_cost += estimated_cost
                total_tax += estimated_tax or 0
                
                trade_proposals.append(TradeProposal(
                    instrument_id=trade_data.get("instrument_id"),
                    ticker=ticker,
                    exchange=exchange,
                    action=action,
                    quantity=abs(quantity),
                    estimated_price=current_price,
                    estimated_cost=estimated_cost,
                    estimated_tax=estimated_tax,
                    source=self.analytics_tool._create_citation("/api/v1/rebalance/simulate", f"{ticker}_{action}")
                ))
            
            # Step 4: Generate explanation
            explanation = self._generate_explanation(
                trade_proposals,
                total_cost,
                total_tax,
                target_alloc
            )
            
            # Step 5: Store in vector store
            context_text = f"Rebalance proposal for user {user_id}: {len(trade_proposals)} trades, total cost ₹{total_cost:,.2f}"
            await self.vector_store.store(
                context_text,
                {
                    "user_id": user_id,
                    "portfolio_id": portfolio_id,
                    "flow_type": "rebalance",
                    "agent_run_id": self.agent_run.id,
                    "trade_count": len(trade_proposals)
                }
            )
            
            # Step 6: Build response
            # Serialize Pydantic models properly
            proposal_data = []
            for tp in trade_proposals:
                if hasattr(tp, 'model_dump'):
                    proposal_data.append(tp.model_dump())
                else:
                    proposal_data.append(tp.dict())
            
            sources_data = []
            for s in self.sources:
                if hasattr(s, 'model_dump'):
                    sources_data.append(s.model_dump())
                else:
                    sources_data.append(s.dict())
            
            output = {
                "proposal": proposal_data,
                "total_estimated_cost": total_cost,
                "total_estimated_tax": total_tax if total_tax > 0 else None,
                "explanation": explanation,
                "sources": sources_data,
                "status": "completed"
            }
            
            await self._update_run_status("completed", output)
            return output
            
        except Exception as e:
            logger.error(f"Rebalance flow error: {e}")
            await self._update_run_status("failed", {"error": str(e)})
            raise
    
    def _generate_explanation(
        self,
        trades: List[TradeProposal],
        total_cost: float,
        total_tax: float,
        target_alloc: Dict[str, float]
    ) -> str:
        """Generate explanation for rebalance proposal"""
        explanation = f"Rebalance Proposal:\n\n"
        explanation += f"Target Allocation: {target_alloc}\n\n"
        explanation += f"Proposed Trades: {len(trades)}\n"
        explanation += f"Total Estimated Cost: ₹{total_cost:,.2f}\n"
        if total_tax > 0:
            explanation += f"Total Estimated Tax: ₹{total_tax:,.2f}\n"
        explanation += "\nTrade Details:\n"
        
        for i, trade in enumerate(trades[:10], 1):  # Show first 10
            explanation += f"{i}. {trade.action} {trade.quantity} shares of {trade.ticker} @ ₹{trade.estimated_price:.2f}\n"
        
        if len(trades) > 10:
            explanation += f"... and {len(trades) - 10} more trades\n"
        
        explanation += "\nThis proposal requires human approval before execution."
        return explanation

