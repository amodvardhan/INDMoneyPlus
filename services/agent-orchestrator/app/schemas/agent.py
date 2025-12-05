"""Pydantic schemas for agent orchestrator"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class AgentRunBase(BaseModel):
    user_id: int
    flow_type: str
    input_json: Dict[str, Any]


class AgentRunCreate(AgentRunBase):
    pass


class AgentRunRead(AgentRunBase):
    id: int
    output_json: Optional[Dict[str, Any]] = None
    status: str
    executed_by: Optional[int] = None
    executed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentActionLogRead(BaseModel):
    id: int
    agent_run_id: int
    step: int
    tool_called: str
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    portfolio_id: int = Field(..., description="Portfolio ID to analyze")
    user_id: int = Field(..., description="User ID requesting analysis")


class SourceCitation(BaseModel):
    service: str
    endpoint: str
    timestamp: datetime
    data_point: str


class Metric(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    source: SourceCitation


class AnalysisResponse(BaseModel):
    agent_run_id: int
    explanation: str = Field(..., description="Human-readable explanation of portfolio analysis")
    metrics: List[Metric] = Field(..., description="Structured metrics with source citations")
    sources: List[SourceCitation] = Field(..., description="All sources used in analysis")
    status: str


class RebalanceRequest(BaseModel):
    portfolio_id: int = Field(..., description="Portfolio ID to rebalance")
    target_alloc: Dict[str, float] = Field(..., description="Target allocation percentages by asset class")
    user_id: int = Field(..., description="User ID requesting rebalance")


class TradeProposal(BaseModel):
    instrument_id: int
    ticker: str
    exchange: str
    action: str  # "BUY" or "SELL"
    quantity: float
    estimated_price: float
    estimated_cost: float
    estimated_tax: Optional[float] = None
    source: SourceCitation


class RebalanceResponse(BaseModel):
    agent_run_id: int
    proposal: List[TradeProposal] = Field(..., description="List of proposed trades")
    total_estimated_cost: float
    total_estimated_tax: Optional[float] = None
    explanation: str = Field(..., description="Rationale for rebalance proposal")
    sources: List[SourceCitation]
    status: str


class ExecutionPrepRequest(BaseModel):
    agent_run_id: int = Field(..., description="Agent run ID from rebalance flow")
    human_confirmation: bool = Field(..., description="Must be true to generate order envelopes")
    user_id: int = Field(..., description="User ID approving execution")


class OrderEnvelope(BaseModel):
    instrument_id: int
    ticker: str
    exchange: str
    action: str  # "BUY" or "SELL"
    quantity: float
    order_type: str = "MARKET"  # MARKET, LIMIT, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_agent_run_id: int


class ExecutionPrepResponse(BaseModel):
    agent_run_id: int
    order_envelopes: List[OrderEnvelope] = Field(..., description="Order envelopes ready for order-orchestrator")
    explanation: str = Field(..., description="Summary of prepared orders")
    requires_approval: bool = True
    status: str


class QueryRequest(BaseModel):
    query: str = Field(..., description="User's question or query")
    user_id: int = Field(..., description="User ID making the query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")


class QueryResponse(BaseModel):
    agent_run_id: int
    answer: str = Field(..., description="Comprehensive answer to the user's query")
    query_type: str = Field(..., description="Type of query (portfolio, stock, ipo, nfo, education, etc.)")
    sources: List[SourceCitation] = Field(default_factory=list, description="Sources used in generating the answer")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested follow-up actions")
    status: str

