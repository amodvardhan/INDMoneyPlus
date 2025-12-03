"""Tests for agent endpoints"""
import pytest
from httpx import AsyncClient, Response
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_analyze_portfolio(client: AsyncClient):
    """Test portfolio analysis flow"""
    with patch("app.core.tools.aggregator_tool.AggregatorTool.get_consolidated_holdings") as mock_holdings, \
         patch("app.core.tools.marketdata_tool.MarketDataTool.get_latest_price") as mock_price, \
         patch("app.core.tools.analytics_tool.AnalyticsTool.compute_portfolio_metrics") as mock_metrics:
        
        # Mock responses
        mock_holdings.return_value = {
            "data": {
                "holdings": [
                    {"ticker": "RELIANCE", "exchange": "NSE", "total_qty": 100, "total_valuation": 255000.00}
                ],
                "total_valuation": 255000.00
            },
            "citation": {"service": "aggregator-service", "endpoint": "/api/v1/holdings/1", "timestamp": "2024-01-01T00:00:00", "data_point": "holdings"}
        }
        
        mock_price.return_value = {
            "data": {"price": 2550.00, "ticker": "RELIANCE", "exchange": "NSE"},
            "citation": {"service": "marketdata-service", "endpoint": "/api/v1/price/RELIANCE/latest", "timestamp": "2024-01-01T00:00:00", "data_point": "price"}
        }
        
        mock_metrics.return_value = {
            "data": {"total_valuation": 255000.00, "holdings_count": 1},
            "citation": {"service": "analytics-service", "endpoint": "/api/v1/portfolio/metrics", "timestamp": "2024-01-01T00:00:00", "data_point": "metrics"}
        }
        
        response = await client.post(
            "/api/v1/agents/analyze",
            json={"portfolio_id": 1, "user_id": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "agent_run_id" in data
        assert "explanation" in data
        assert "metrics" in data
        assert "sources" in data
        assert len(data["sources"]) > 0


@pytest.mark.asyncio
async def test_rebalance_portfolio(client: AsyncClient):
    """Test rebalance flow"""
    with patch("app.core.tools.aggregator_tool.AggregatorTool.get_consolidated_holdings") as mock_holdings, \
         patch("app.core.tools.analytics_tool.AnalyticsTool.simulate_rebalance") as mock_rebalance, \
         patch("app.core.tools.marketdata_tool.MarketDataTool.get_latest_price") as mock_price:
        
        mock_holdings.return_value = {
            "data": {
                "holdings": [{"ticker": "RELIANCE", "exchange": "NSE", "total_qty": 100}],
                "total_valuation": 255000.00
            },
            "citation": {}
        }
        
        mock_rebalance.return_value = {
            "data": {
                "trades": [
                    {
                        "instrument_id": 1,
                        "ticker": "TCS",
                        "exchange": "NSE",
                        "action": "BUY",
                        "quantity": 50,
                        "estimated_price": 3500.00,
                        "estimated_tax": 100.00
                    }
                ]
            },
            "citation": {}
        }
        
        mock_price.return_value = {
            "data": {"price": 3500.00},
            "citation": {}
        }
        
        response = await client.post(
            "/api/v1/agents/rebalance",
            json={
                "portfolio_id": 1,
                "user_id": 1,
                "target_alloc": {"EQUITY": 0.6, "BOND": 0.4}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "agent_run_id" in data
        assert "proposal" in data
        assert len(data["proposal"]) > 0
        assert "total_estimated_cost" in data


@pytest.mark.asyncio
async def test_prepare_execution(client: AsyncClient, db_session):
    """Test execution preparation flow"""
    from app.models.agent import AgentRun
    
    # Create a rebalance run first
    rebalance_run = AgentRun(
        user_id=1,
        flow_type="rebalance",
        input_json={"portfolio_id": 1, "target_alloc": {}},
        output_json={
            "proposal": [
                {
                    "instrument_id": 1,
                    "ticker": "TCS",
                    "exchange": "NSE",
                    "action": "BUY",
                    "quantity": 50,
                    "estimated_price": 3500.00
                }
            ]
        },
        status="completed"
    )
    db_session.add(rebalance_run)
    await db_session.commit()
    await db_session.refresh(rebalance_run)
    
    with patch("app.core.tools.order_tool.OrderTool.validate_order_envelope") as mock_validate:
        mock_validate.return_value = {
            "data": {"valid": True},
            "citation": {}
        }
        
        response = await client.post(
            "/api/v1/agents/prepare_execution",
            json={
                "agent_run_id": rebalance_run.id,
                "user_id": 1,
                "human_confirmation": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "agent_run_id" in data
        assert "order_envelopes" in data
        assert len(data["order_envelopes"]) > 0
        assert data["requires_approval"] is True


@pytest.mark.asyncio
async def test_prepare_execution_requires_confirmation(client: AsyncClient):
    """Test that execution prep requires human confirmation"""
    response = await client.post(
        "/api/v1/agents/prepare_execution",
        json={
            "agent_run_id": 1,
            "user_id": 1,
            "human_confirmation": False
        }
    )
    
    assert response.status_code == 400
    assert "human_confirmation" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_agent_logs(client: AsyncClient, db_session):
    """Test getting agent action logs"""
    from app.models.agent import AgentRun, AgentActionLog
    
    agent_run = AgentRun(
        user_id=1,
        flow_type="analysis",
        input_json={},
        status="completed"
    )
    db_session.add(agent_run)
    await db_session.commit()
    await db_session.refresh(agent_run)
    
    action_log = AgentActionLog(
        agent_run_id=agent_run.id,
        step=1,
        tool_called="aggregator.get_holdings",
        tool_input={},
        tool_output={}
    )
    db_session.add(action_log)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/agents/{agent_run.id}/logs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tool_called"] == "aggregator.get_holdings"

