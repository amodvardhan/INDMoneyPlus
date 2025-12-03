"""Kafka producer for emitting events"""
import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory Kafka producer (would use kafka-python or confluent-kafka in production)
_kafka_producer = None


class KafkaProducer:
    """Kafka producer for emitting events"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._events = []  # Store events in memory for testing
    
    async def send(self, topic: str, key: Optional[str], value: Dict[str, Any]) -> None:
        """Send event to Kafka topic"""
        try:
            # In production, this would use actual Kafka client
            # For now, log and store in memory
            event = {
                "topic": topic,
                "key": key,
                "value": value,
                "timestamp": str(logging.Formatter().formatTime(logging.LogRecord(
                    name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
                )))
            }
            self._events.append(event)
            logger.info(f"Kafka event sent to {topic}: {json.dumps(value)}")
        except Exception as e:
            logger.error(f"Failed to send Kafka event: {e}")
            raise


def get_kafka_producer() -> KafkaProducer:
    """Get Kafka producer instance"""
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaProducer(settings.kafka_bootstrap_servers)
    return _kafka_producer

