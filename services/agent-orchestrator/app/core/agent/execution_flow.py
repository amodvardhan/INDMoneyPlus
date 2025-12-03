"""Execution-Prep Flow agent"""
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.agent.agent_base import BaseAgentFlow
from app.models.agent import AgentRun
from app.schemas.agent import OrderEnvelope, SourceCitation

logger = logging.getLogger(__name__)


class ExecutionPrepFlow(BaseAgentFlow):
    """Agent flow for preparing execution-ready order envelopes"""
    
    async def execute(
        self,
        agent_run_id: int,
        user_id: int,
        human_confirmation: bool
    ) -> Dict[str, Any]:
        """Execute execution-prep flow"""
        if not human_confirmation:
            await self._update_run_status("failed", {
                "error": "Human confirmation required for execution preparation",
                "order_envelopes": []
            })
            raise ValueError("Human confirmation is required to prepare order envelopes")
        
        await self._initialize()
        
        try:
            # Step 1: Fetch the rebalance proposal from previous agent run
            result = await self.db.execute(
                select(AgentRun).where(AgentRun.id == agent_run_id)
            )
            source_run = result.scalar_one_or_none()
            
            if not source_run:
                raise ValueError(f"Source agent run {agent_run_id} not found")
            
            if source_run.flow_type != "rebalance":
                raise ValueError(f"Source agent run must be of type 'rebalance', got '{source_run.flow_type}'")
            
            if source_run.status != "completed":
                raise ValueError(f"Source agent run must be completed, got status '{source_run.status}'")
            
            output_json = source_run.output_json or {}
            proposal = output_json.get("proposal", [])
            
            if not proposal:
                await self._update_run_status("completed", {
                    "order_envelopes": [],
                    "explanation": "No trades to prepare for execution",
                    "status": "completed"
                })
                return self.agent_run.output_json
            
            # Step 2: Convert trade proposals to order envelopes
            order_envelopes: List[OrderEnvelope] = []
            
            for trade in proposal:
                # Validate order envelope
                envelope_dict = {
                    "instrument_id": trade.get("instrument_id"),
                    "ticker": trade.get("ticker"),
                    "exchange": trade.get("exchange"),
                    "action": trade.get("action"),
                    "quantity": trade.get("quantity"),
                    "order_type": "MARKET",
                    "metadata": {
                        "estimated_price": trade.get("estimated_price"),
                        "estimated_cost": trade.get("estimated_cost"),
                        "source_agent_run_id": agent_run_id
                    }
                }
                
                try:
                    # Validate with order orchestrator
                    validation_result = await self.order_tool.validate_order_envelope(envelope_dict)
                    await self._log_action(
                        "order.validate_order_envelope",
                        {"ticker": trade.get("ticker")},
                        validation_result
                    )
                except Exception as e:
                    logger.warning(f"Order validation failed for {trade.get('ticker')}: {e}")
                    # Continue anyway - validation is advisory
                
                order_envelopes.append(OrderEnvelope(
                    instrument_id=trade.get("instrument_id"),
                    ticker=trade.get("ticker"),
                    exchange=trade.get("exchange"),
                    action=trade.get("action"),
                    quantity=trade.get("quantity"),
                    order_type="MARKET",
                    metadata=envelope_dict["metadata"],
                    source_agent_run_id=agent_run_id
                ))
            
            # Step 3: Generate explanation
            explanation = self._generate_explanation(order_envelopes, source_run.id)
            
            # Step 4: Store in vector store
            context_text = f"Execution preparation for user {user_id}: {len(order_envelopes)} order envelopes prepared"
            await self.vector_store.store(
                context_text,
                {
                    "user_id": user_id,
                    "flow_type": "execution_prep",
                    "agent_run_id": self.agent_run.id,
                    "source_agent_run_id": agent_run_id,
                    "order_count": len(order_envelopes)
                }
            )
            
            # Step 5: Build response
            output = {
                "order_envelopes": [oe.dict() for oe in order_envelopes],
                "explanation": explanation,
                "requires_approval": True,
                "status": "pending_approval"
            }
            
            await self._update_run_status("pending_approval", output)
            return output
            
        except Exception as e:
            logger.error(f"Execution-prep flow error: {e}")
            await self._update_run_status("failed", {"error": str(e)})
            raise
    
    def _generate_explanation(self, envelopes: List[OrderEnvelope], source_run_id: int) -> str:
        """Generate explanation for prepared orders"""
        explanation = f"Execution Preparation Summary:\n\n"
        explanation += f"Source Rebalance Run ID: {source_run_id}\n"
        explanation += f"Order Envelopes Prepared: {len(envelopes)}\n\n"
        
        buy_count = sum(1 for e in envelopes if e.action == "BUY")
        sell_count = sum(1 for e in envelopes if e.action == "SELL")
        
        explanation += f"Buy Orders: {buy_count}\n"
        explanation += f"Sell Orders: {sell_count}\n\n"
        
        explanation += "Order Envelopes:\n"
        for i, envelope in enumerate(envelopes[:10], 1):
            explanation += f"{i}. {envelope.action} {envelope.quantity} shares of {envelope.ticker} ({envelope.exchange})\n"
        
        if len(envelopes) > 10:
            explanation += f"... and {len(envelopes) - 10} more orders\n"
        
        explanation += "\nThese order envelopes are ready for submission to order-orchestrator after final approval."
        return explanation

