"""Database models for order orchestrator"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, nullable=False, index=True)
    broker = Column(String, nullable=False, index=True)  # zerodha-mock, alpaca-mock
    instrument_id = Column(Integer, nullable=False, index=True)
    qty = Column(Float, nullable=False)
    price_limit = Column(Float, nullable=True)  # For limit orders
    side = Column(String, nullable=False, index=True)  # BUY, SELL
    status = Column(String, nullable=False, default="placed", index=True)  # placed, acked, filled, settled, cancelled, rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    executed_at = Column(DateTime, nullable=True)
    ext_order_id = Column(String, nullable=True, index=True)  # External order ID from broker
    fill_price = Column(Float, nullable=True)
    fill_qty = Column(Float, nullable=True)
    batch_id = Column(Integer, ForeignKey("order_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    batch = relationship("OrderBatch", back_populates="orders")
    
    __table_args__ = (
        Index('ix_orders_portfolio_status', 'portfolio_id', 'status'),
        Index('ix_orders_broker_status', 'broker', 'status'),
    )


class OrderBatch(Base):
    __tablename__ = "order_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    portfolio_id = Column(Integer, nullable=False, index=True)
    orders_json = Column(JSON, nullable=False)  # Original order requests
    status = Column(String, nullable=False, default="pending", index=True)  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    idempotency_key = Column(String, nullable=True, unique=True, index=True)
    
    # Relationships
    orders = relationship("Order", back_populates="batch", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_order_batches_user_portfolio', 'user_id', 'portfolio_id'),
    )


class BrokerConnectorConfig(Base):
    __tablename__ = "broker_connector_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    broker_name = Column(String, unique=True, nullable=False, index=True)  # zerodha-mock, alpaca-mock
    config_json = Column(JSON, nullable=False)  # Broker-specific configuration
    active = Column(String, nullable=False, default="true")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

