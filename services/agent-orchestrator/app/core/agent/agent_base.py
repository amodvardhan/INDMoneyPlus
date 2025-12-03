"""Base agent flow implementation"""
import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.tools import MarketDataTool, AnalyticsTool, AggregatorTool, OrderTool
from app.core.vector_store import get_vector_store
from app.models.agent import AgentRun, AgentActionLog
from app.schemas.agent import SourceCitation

logger = logging.getLogger(__name__)


class BaseAgentFlow:
    """Base class for agent flows"""
    
    def __init__(self, db: AsyncSession, agent_run: AgentRun):
        self.db = db
        self.agent_run = agent_run
        self.marketdata_tool = MarketDataTool()
        self.analytics_tool = AnalyticsTool()
        self.aggregator_tool = AggregatorTool()
        self.order_tool = OrderTool()
        self.vector_store = None
        self.step_counter = 0
        self.sources: List[SourceCitation] = []
    
    async def _initialize(self):
        """Initialize vector store"""
        self.vector_store = await get_vector_store()
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """Recursively serialize objects for JSON storage"""
        # Check for datetime first (before BaseModel, as datetime might be inside BaseModel)
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, BaseModel):
            # Convert BaseModel to dict first, then recursively serialize to catch nested datetimes
            if hasattr(obj, 'model_dump'):
                # Pydantic v2 - convert to dict, then recursively serialize
                model_dict = obj.model_dump()
            else:
                # Pydantic v1 - convert to dict, then recursively serialize
                model_dict = obj.dict()
            # Recursively serialize the dict to handle nested datetime objects
            return self._serialize_for_json(model_dict)
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        else:
            return obj

    async def _log_action(
        self,
        tool_called: str,
        tool_input: Dict[str, Any],
        tool_output: Dict[str, Any]
    ):
        """Log agent action to database"""
        self.step_counter += 1
        
        # Serialize tool_output to ensure all Pydantic models are converted to dicts
        serialized_output = self._serialize_for_json(tool_output)
        serialized_input = self._serialize_for_json(tool_input)
        
        action_log = AgentActionLog(
            agent_run_id=self.agent_run.id,
            step=self.step_counter,
            tool_called=tool_called,
            tool_input=serialized_input,
            tool_output=serialized_output
        )
        self.db.add(action_log)
        await self.db.flush()
        
        # Collect source citation from original tool_output (before serialization)
        if "citation" in tool_output:
            citation = tool_output["citation"]
            if isinstance(citation, BaseModel):
                self.sources.append(citation)
            elif isinstance(citation, dict):
                # If it's already a dict, convert to SourceCitation for consistency
                self.sources.append(SourceCitation(**citation))
            else:
                logger.warning(f"Unexpected citation type: {type(citation)}")
    
    async def _update_run_status(self, status: str, output_json: Dict[str, Any] = None):
        """Update agent run status"""
        self.agent_run.status = status
        if output_json:
            self.agent_run.output_json = output_json
        await self.db.commit()
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the agent flow - to be implemented by subclasses"""
        raise NotImplementedError

