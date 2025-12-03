"""Kafka event publishing"""
import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_kafka_producer = None


async def get_kafka_producer():
    """Get or create Kafka producer"""
    global _kafka_producer
    
    if not settings.kafka_enabled:
        return None
    
    if _kafka_producer is None:
        try:
            from aiokafka import AIOKafkaProducer
            _kafka_producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers
            )
            await _kafka_producer.start()
            logger.info("Kafka producer initialized")
        except ImportError:
            logger.warning("aiokafka not installed. Events will not be published.")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            return None
    
    return _kafka_producer


async def publish_order_event(event_type: str, payload: Dict[str, Any]):
    """
    Publish order event to Kafka
    
    Args:
        event_type: Event type (order.placed, order.acked, order.filled, etc.)
        payload: Event payload
    """
    if not settings.kafka_enabled:
        logger.debug(f"Kafka disabled. Event {event_type} not published.")
        return
    
    producer = await get_kafka_producer()
    if not producer:
        logger.debug(f"Kafka producer not available. Event {event_type} not published.")
        return
    
    try:
        event = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": payload.get("timestamp")
        }
        
        await producer.send_and_wait(
            settings.kafka_topic_orders,
            json.dumps(event).encode()
        )
        logger.info(f"Published event: {event_type}")
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")


async def close_kafka_producer():
    """Close Kafka producer"""
    global _kafka_producer
    if _kafka_producer:
        await _kafka_producer.stop()
        _kafka_producer = None

