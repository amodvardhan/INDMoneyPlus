"""Base transport interface"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TransportResult:
    """Result from transport send operation"""
    success: bool
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseTransport(ABC):
    """Base class for notification transports"""
    
    @abstractmethod
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransportResult:
        """
        Send notification
        
        Args:
            recipient: Recipient address (email, phone, device token)
            subject: Subject line (for email)
            body: Message body
            metadata: Additional metadata
            
        Returns:
            TransportResult with success status and response details
        """
        pass

