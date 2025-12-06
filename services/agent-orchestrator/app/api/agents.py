"""Agent endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.core.agent import AnalysisFlow, RebalanceFlow, ExecutionPrepFlow, QueryFlow, RecommendationsFlow
from app.models.agent import AgentRun, AgentActionLog
from app.schemas.agent import (
    AnalysisRequest,
    AnalysisResponse,
    RebalanceRequest,
    RebalanceResponse,
    ExecutionPrepRequest,
    ExecutionPrepResponse,
    QueryRequest,
    QueryResponse,
    RecommendationsRequest,
    RecommendationsResponse,
    StockRecommendation,
    AgentRunRead,
    AgentActionLogRead,
)

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_portfolio(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute portfolio analysis flow"""
    # Create agent run
    agent_run = AgentRun(
        user_id=request.user_id,
        flow_type="analysis",
        input_json={"portfolio_id": request.portfolio_id},
        status="running"
    )
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)
    
    try:
        # Execute analysis flow
        flow = AnalysisFlow(db, agent_run)
        result = await flow.execute(request.portfolio_id, request.user_id)
        
        # Ensure all required keys are present
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict result, got {type(result)}")
        
        required_keys = ["explanation", "metrics", "sources", "status"]
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            raise ValueError(f"Result missing required keys: {missing_keys}")
        
        return AnalysisResponse(
            agent_run_id=agent_run.id,
            explanation=result["explanation"],
            metrics=result["metrics"],
            sources=result["sources"],
            status=result["status"]
        )
    except Exception as e:
        # Rollback the session if there was a database error
        try:
            await db.rollback()
        except Exception:
            pass
        # Try to update agent run status to failed
        try:
            agent_run.status = "failed"
            await db.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/rebalance", response_model=RebalanceResponse)
async def rebalance_portfolio(
    request: RebalanceRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute rebalance proposal flow"""
    # Create agent run
    agent_run = AgentRun(
        user_id=request.user_id,
        flow_type="rebalance",
        input_json={
            "portfolio_id": request.portfolio_id,
            "target_alloc": request.target_alloc
        },
        status="running"
    )
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)
    
    try:
        # Execute rebalance flow
        flow = RebalanceFlow(db, agent_run)
        result = await flow.execute(
            request.portfolio_id,
            request.user_id,
            request.target_alloc
        )
        
        # Ensure all required keys are present
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict result, got {type(result)}")
        
        required_keys = ["proposal", "total_estimated_cost", "explanation", "sources", "status"]
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            raise ValueError(f"Result missing required keys: {missing_keys}")
        
        return RebalanceResponse(
            agent_run_id=agent_run.id,
            proposal=result["proposal"],
            total_estimated_cost=result["total_estimated_cost"],
            total_estimated_tax=result.get("total_estimated_tax"),
            explanation=result["explanation"],
            sources=result["sources"],
            status=result["status"]
        )
    except Exception as e:
        # Rollback the session if there was a database error
        try:
            await db.rollback()
        except Exception:
            pass
        # Try to update agent run status to failed
        try:
            agent_run.status = "failed"
            await db.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rebalance failed: {str(e)}"
        )


@router.post("/prepare_execution", response_model=ExecutionPrepResponse)
async def prepare_execution(
    request: ExecutionPrepRequest,
    db: AsyncSession = Depends(get_db)
):
    """Prepare execution-ready order envelopes from approved rebalance proposal"""
    if not request.human_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="human_confirmation must be true to prepare execution"
        )
    
    # Create agent run
    agent_run = AgentRun(
        user_id=request.user_id,
        flow_type="execution_prep",
        input_json={
            "source_agent_run_id": request.agent_run_id,
            "human_confirmation": request.human_confirmation
        },
        status="running",
        executed_by=request.user_id
    )
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)
    
    try:
        # Execute execution-prep flow
        flow = ExecutionPrepFlow(db, agent_run)
        result = await flow.execute(
            request.agent_run_id,
            request.user_id,
            request.human_confirmation
        )
        
        return ExecutionPrepResponse(
            agent_run_id=agent_run.id,
            order_envelopes=result["order_envelopes"],
            explanation=result["explanation"],
            requires_approval=result["requires_approval"],
            status=result["status"]
        )
    except ValueError as e:
        await db.refresh(agent_run)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.refresh(agent_run)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution preparation failed: {str(e)}"
        )


@router.get("/{agent_run_id}/logs", response_model=List[AgentActionLogRead])
async def get_agent_logs(
    agent_run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get action logs for an agent run"""
    # Verify agent run exists
    result = await db.execute(
        select(AgentRun).where(AgentRun.id == agent_run_id)
    )
    agent_run = result.scalar_one_or_none()
    
    if not agent_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent run {agent_run_id} not found"
        )
    
    # Get action logs
    result = await db.execute(
        select(AgentActionLog)
        .where(AgentActionLog.agent_run_id == agent_run_id)
        .order_by(AgentActionLog.step)
    )
    logs = result.scalars().all()
    
    return logs


@router.post("/query", response_model=QueryResponse)
async def query_assistant(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Handle general queries about stocks, portfolio, IPOs, NFOs, and market education"""
    # Create agent run
    agent_run = AgentRun(
        user_id=request.user_id,
        flow_type="query",
        input_json={
            "query": request.query,
            "context": request.context or {}
        },
        status="running"
    )
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)
    
    try:
        # Execute query flow
        flow = QueryFlow(db, agent_run)
        result = await flow.execute(
            request.query,
            request.user_id,
            request.context
        )
        
        # Ensure all required keys are present
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict result, got {type(result)}")
        
        required_keys = ["answer", "query_type", "sources", "status"]
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            raise ValueError(f"Result missing required keys: {missing_keys}")
        
        return QueryResponse(
            agent_run_id=agent_run.id,
            answer=result["answer"],
            query_type=result["query_type"],
            sources=result.get("sources", []),
            suggested_actions=result.get("suggested_actions", []),
            status=result["status"]
        )
    except Exception as e:
        # Rollback the session if there was a database error
        try:
            await db.rollback()
        except Exception:
            pass
        # Try to update agent run status to failed
        try:
            agent_run.status = "failed"
            await db.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/recommendations", response_model=RecommendationsResponse)
async def generate_recommendations(
    request: RecommendationsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate dynamic stock recommendations using AI analysis"""
    # Create agent run
    agent_run = AgentRun(
        user_id=0,  # System-generated recommendations
        flow_type="recommendations",
        input_json={
            "limit": request.limit,
            "tickers": request.tickers,
            "exchanges": request.exchanges
        },
        status="running"
    )
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)
    
    try:
        # Execute recommendations flow
        flow = RecommendationsFlow(db, agent_run)
        result = await flow.execute(
            limit=request.limit,
            tickers=request.tickers,
            exchanges=request.exchanges
        )
        
        # Convert recommendations to StockRecommendation models
        recommendations = []
        for rec in result.get("recommendations", []):
            recommendations.append(StockRecommendation(**rec))
        
        return RecommendationsResponse(
            agent_run_id=agent_run.id,
            recommendations=recommendations,
            market_condition=result.get("market_condition", "unknown"),
            generated_at=result.get("generated_at", datetime.utcnow().isoformat()),
            sources=result.get("sources", []),
            status=result.get("status", "completed")
        )
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        try:
            agent_run.status = "failed"
            await db.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendations generation failed: {str(e)}"
        )


@router.get("/{agent_run_id}", response_model=AgentRunRead)
async def get_agent_run(
    agent_run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get agent run details"""
    result = await db.execute(
        select(AgentRun).where(AgentRun.id == agent_run_id)
    )
    agent_run = result.scalar_one_or_none()
    
    if not agent_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent run {agent_run_id} not found"
        )
    
    return agent_run

