"""Base tool interface"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from app.schemas.agent import SourceCitation


class BaseTool(ABC):
    """Base class for service tool adapters"""
    
    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url
    
    def _create_citation(self, endpoint: str, data_point: str) -> SourceCitation:
        """Create source citation for tool output"""
        return SourceCitation(
            service=self.service_name,
            endpoint=endpoint,
            timestamp=datetime.utcnow(),
            data_point=data_point
        )
    
    @abstractmethod
    async def call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP call to service and return response with citation"""
        pass

