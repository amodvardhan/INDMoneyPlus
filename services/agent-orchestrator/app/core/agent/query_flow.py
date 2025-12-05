"""Query Flow agent for handling general questions"""
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.agent.agent_base import BaseAgentFlow
from app.models.agent import AgentRun
from app.schemas.agent import SourceCitation
from app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class QueryFlow(BaseAgentFlow):
    """Agent flow for handling general queries about stocks, portfolio, IPOs, NFOs, and market education"""
    
    def __init__(self, db: AsyncSession, agent_run: AgentRun):
        super().__init__(db, agent_run)
        self.llm = None
        if settings.openai_api_key:
            self.llm = ChatOpenAI(
                model=settings.openai_model or "gpt-4",
                temperature=0.7,
                api_key=settings.openai_api_key
            )
    
    async def execute(self, query: str, user_id: int, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute query flow"""
        await self._initialize()
        
        try:
            # Step 1: Determine query type and gather relevant data
            query_type = self._classify_query(query)
            await self._log_action(
                "query.classify",
                {"query": query},
                {"query_type": query_type}
            )
            
            # Step 2: Gather context based on query type
            context_data = await self._gather_context(query_type, query, user_id, context)
            await self._log_action(
                "query.gather_context",
                {"query_type": query_type},
                {"context_keys": list(context_data.keys())}
            )
            
            # Step 3: Generate response using LLM with context
            response = await self._generate_response(query, query_type, context_data, user_id)
            
            # Step 4: Store query and response in vector store for future reference
            context_text = f"User query: {query}\nResponse: {response['answer']}"
            await self.vector_store.store(
                context_text,
                {
                    "user_id": user_id,
                    "query": query,
                    "query_type": query_type,
                    "flow_type": "query",
                    "agent_run_id": self.agent_run.id
                }
            )
            
            # Step 5: Build response
            output = {
                "answer": response['answer'],
                "query_type": query_type,
                "sources": response.get('sources', []),
                "suggested_actions": response.get('suggested_actions', []),
                "status": "completed"
            }
            
            await self._update_run_status("completed", output)
            return output
            
        except Exception as e:
            logger.error(f"Query flow error: {e}")
            await self._update_run_status("failed", {"error": str(e)})
            raise
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        # Portfolio-related queries
        if any(word in query_lower for word in ['portfolio', 'holdings', 'my investments', 'my stocks']):
            return "portfolio"
        
        # Stock-specific queries
        if any(word in query_lower for word in ['stock', 'share', 'ticker', 'price', 'quote']):
            return "stock"
        
        # IPO queries
        if any(word in query_lower for word in ['ipo', 'initial public offering', 'new listing']):
            return "ipo"
        
        # NFO queries
        if any(word in query_lower for word in ['nfo', 'new fund offering', 'mutual fund']):
            return "nfo"
        
        # Rebalancing queries
        if any(word in query_lower for word in ['rebalance', 'rebalancing', 'allocation', 'diversification']):
            return "rebalancing"
        
        # Educational queries
        if any(word in query_lower for word in ['what is', 'how does', 'explain', 'learn', 'understand', 'meaning']):
            return "education"
        
        # Market queries
        if any(word in query_lower for word in ['market', 'indices', 'nifty', 'sensex', 's&p', 'dow']):
            return "market"
        
        # Tax queries
        if any(word in query_lower for word in ['tax', 'capital gains', 'taxation', 'ltcg', 'stcg']):
            return "tax"
        
        # Default to general
        return "general"
    
    async def _gather_context(
        self,
        query_type: str,
        query: str,
        user_id: int,
        provided_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Gather relevant context based on query type"""
        context = {}
        
        try:
            # Portfolio context
            if query_type == "portfolio":
                holdings_result = await self.aggregator_tool.get_consolidated_holdings(user_id)
                context['holdings'] = holdings_result.get("data", {})
                await self._log_action(
                    "aggregator.get_consolidated_holdings",
                    {"user_id": user_id},
                    {"holdings_count": len(holdings_result.get("data", {}).get("holdings", []))}
                )
            
            # Stock-specific context
            if query_type == "stock":
                # Try to extract ticker from query
                ticker = self._extract_ticker(query)
                if ticker:
                    try:
                        # Try common exchanges
                        for exchange in ["NSE", "BSE", "NYSE", "NASDAQ"]:
                            try:
                                instrument = await self.marketdata_tool.get_instrument(ticker, exchange)
                                context['instrument'] = instrument.get("data", {})
                                price = await self.marketdata_tool.get_latest_price(ticker, exchange)
                                context['price'] = price.get("data", {})
                                break
                            except:
                                continue
                    except Exception as e:
                        logger.warning(f"Could not fetch stock data: {e}")
            
            # Add provided context
            if provided_context:
                context.update(provided_context)
            
        except Exception as e:
            logger.warning(f"Error gathering context: {e}")
        
        return context
    
    def _extract_ticker(self, query: str) -> Optional[str]:
        """Extract ticker symbol from query"""
        import re
        # Look for uppercase ticker patterns (3-5 letters)
        matches = re.findall(r'\b[A-Z]{3,5}\b', query.upper())
        if matches:
            return matches[0]
        return None
    
    async def _generate_response(
        self,
        query: str,
        query_type: str,
        context: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Generate response using LLM with context"""
        
        # Build system prompt based on query type
        system_prompt = self._build_system_prompt(query_type, context)
        
        # Build context string
        context_str = self._format_context(context)
        
        if self.llm:
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Context:\n{context_str}\n\nUser Question: {query}\n\nPlease provide a comprehensive, accurate, and helpful answer.")
                ]
                
                response = await self.llm.ainvoke(messages)
                answer = response.content
                
                # Extract sources from context
                sources = []
                if 'holdings' in context:
                    sources.append(SourceCitation(
                        service="aggregator-service",
                        endpoint=f"/api/v1/holdings/{user_id}",
                        timestamp=self.agent_run.created_at,
                        data_point="portfolio_holdings"
                    ))
                if 'instrument' in context or 'price' in context:
                    sources.append(SourceCitation(
                        service="marketdata-service",
                        endpoint="/api/v1/instruments",
                        timestamp=self.agent_run.created_at,
                        data_point="market_data"
                    ))
                
                # Generate suggested actions
                suggested_actions = self._generate_suggested_actions(query_type, context)
                
                return {
                    "answer": answer,
                    "sources": [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in sources],
                    "suggested_actions": suggested_actions
                }
            except Exception as e:
                logger.error(f"LLM error: {e}")
                # Fallback to structured response
                return self._generate_fallback_response(query, query_type, context)
        else:
            # No LLM available, use fallback
            return self._generate_fallback_response(query, query_type, context)
    
    def _build_system_prompt(self, query_type: str, context: Dict[str, Any]) -> str:
        """Build system prompt based on query type"""
        base_prompt = """You are an expert financial advisor and portfolio management assistant. You help users understand:
- Portfolio management and investment strategies
- Stock market concepts and terminology
- IPOs (Initial Public Offerings) and NFOs (New Fund Offerings)
- Rebalancing and asset allocation
- Tax implications of investments
- General market education

Always provide accurate, helpful, and educational responses. If you don't know something, say so. Never provide financial advice that could be construed as personalized investment recommendations without proper disclaimers.

Format your responses clearly with:
- Clear explanations
- Examples when helpful
- Relevant context from the user's portfolio when available
- Actionable insights when appropriate
"""
        
        if query_type == "portfolio":
            base_prompt += "\n\nFocus on the user's portfolio holdings and provide insights specific to their investments."
        elif query_type == "stock":
            base_prompt += "\n\nProvide detailed information about stocks, including price data, company information, and market analysis."
        elif query_type == "ipo":
            base_prompt += "\n\nExplain IPOs comprehensively, including the process, risks, benefits, and how to participate."
        elif query_type == "nfo":
            base_prompt += "\n\nExplain NFOs (New Fund Offerings) including types, benefits, risks, and how they differ from existing funds."
        elif query_type == "education":
            base_prompt += "\n\nProvide educational explanations that help users learn and understand investment concepts."
        
        return base_prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context data for LLM"""
        context_parts = []
        
        if 'holdings' in context:
            holdings = context['holdings'].get('holdings', [])
            if holdings:
                context_parts.append(f"User's Portfolio Holdings ({len(holdings)} holdings):")
                for holding in holdings[:10]:  # Limit to top 10
                    ticker = holding.get('ticker', 'N/A')
                    qty = holding.get('total_qty', 0)
                    val = holding.get('total_valuation', 0)
                    context_parts.append(f"- {ticker}: {qty} shares, Value: ₹{val:,.2f}")
        
        if 'instrument' in context:
            inst = context['instrument']
            context_parts.append(f"\nStock Information:")
            context_parts.append(f"- Ticker: {inst.get('ticker', 'N/A')}")
            context_parts.append(f"- Name: {inst.get('name', 'N/A')}")
            context_parts.append(f"- Exchange: {inst.get('exchange', 'N/A')}")
        
        if 'price' in context:
            price = context['price']
            context_parts.append(f"\nCurrent Price: ₹{price.get('close', 'N/A')}")
        
        return "\n".join(context_parts) if context_parts else "No specific context available."
    
    def _generate_suggested_actions(self, query_type: str, context: Dict[str, Any]) -> List[str]:
        """Generate suggested follow-up actions"""
        actions = []
        
        if query_type == "portfolio":
            actions.extend([
                "View detailed portfolio analysis",
                "Generate rebalancing proposal",
                "Check individual holdings"
            ])
        elif query_type == "stock":
            actions.extend([
                "View stock price chart",
                "Check company fundamentals",
                "Add to watchlist"
            ])
        elif query_type == "ipo":
            actions.extend([
                "Check upcoming IPOs",
                "Learn about IPO application process",
                "Review IPO performance history"
            ])
        elif query_type == "rebalancing":
            actions.extend([
                "Set target allocation",
                "Generate rebalance proposal",
                "Review current allocation"
            ])
        
        return actions
    
    def _generate_fallback_response(self, query: str, query_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback response when LLM is not available"""
        responses = {
            "portfolio": "I can help you understand your portfolio. To get detailed analysis, please use the 'Analyze Portfolio' feature. I can answer questions about portfolio management, diversification, and investment strategies.",
            "stock": "I can help you understand stocks and market data. For specific stock prices and information, please check the market data section. I can explain stock market concepts, how stocks work, and investment strategies.",
            "ipo": "An IPO (Initial Public Offering) is when a private company offers its shares to the public for the first time. Companies use IPOs to raise capital. Investors can apply during the IPO period, and shares are allocated via lottery. IPOs can offer high returns but also carry higher risk. Would you like to know more about a specific aspect of IPOs?",
            "nfo": "An NFO (New Fund Offering) is when a mutual fund company launches a new scheme. NFOs start with NAV of ₹10. They don't have a track record yet, so research the fund house and fund manager. Consider expense ratios and investment strategy before investing.",
            "rebalancing": "Rebalancing is adjusting your portfolio back to your target allocation. It helps maintain your desired risk level and can improve returns over time. You can set target allocations and generate rebalancing proposals using the Rebalance feature.",
            "education": "I'm here to help you learn about investing! I can explain concepts like stocks, bonds, ETFs, portfolio management, risk, diversification, and more. What specific topic would you like to learn about?",
            "general": "I'm your AI portfolio assistant. I can help with questions about your portfolio, stocks, IPOs, NFOs, rebalancing, and general investment education. What would you like to know?"
        }
        
        answer = responses.get(query_type, responses["general"])
        
        # Add context-specific information
        if 'holdings' in context:
            holdings_count = len(context['holdings'].get('holdings', []))
            if holdings_count > 0:
                answer += f"\n\nI can see you have {holdings_count} holdings in your portfolio. Would you like me to analyze them?"
        
        return {
            "answer": answer,
            "sources": [],
            "suggested_actions": []
        }

