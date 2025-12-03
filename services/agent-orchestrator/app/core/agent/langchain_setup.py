"""LangChain agent setup with function calling"""
import json
import logging
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.config import settings

logger = logging.getLogger(__name__)


class LangChainAgent:
    """LangChain agent with function calling for deterministic outputs"""
    
    def __init__(self, tools: List[StructuredTool], system_prompt: str):
        self.tools = tools
        self.system_prompt = system_prompt
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            api_key=settings.openai_api_key
        ) if settings.openai_api_key else None
        
        if not self.llm:
            logger.warning("OpenAI API key not set. Agent will use structured execution without LLM.")
    
    def create_agent_executor(self) -> Optional[AgentExecutor]:
        """Create LangChain agent executor"""
        if not self.llm:
            return None
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        return executor
    
    async def run(self, input_text: str) -> Dict[str, Any]:
        """Run agent with input"""
        if self.llm:
            executor = self.create_agent_executor()
            if executor:
                result = await executor.ainvoke({"input": input_text})
                return {"output": result.get("output", ""), "intermediate_steps": result.get("intermediate_steps", [])}
        
        # Fallback: structured execution without LLM
        return {"output": "LLM not configured. Using structured execution.", "intermediate_steps": []}


def create_tool_from_function(func, name: str, description: str) -> StructuredTool:
    """Create LangChain tool from Python function"""
    return StructuredTool.from_function(
        func=func,
        name=name,
        description=description
    )

