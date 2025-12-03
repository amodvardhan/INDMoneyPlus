"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create order_batches table
    op.create_table(
        'order_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('orders_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('idempotency_key', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_batches_id'), 'order_batches', ['id'], unique=False)
    op.create_index(op.f('ix_order_batches_user_id'), 'order_batches', ['user_id'], unique=False)
    op.create_index(op.f('ix_order_batches_portfolio_id'), 'order_batches', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_order_batches_status'), 'order_batches', ['status'], unique=False)
    op.create_index(op.f('ix_order_batches_created_at'), 'order_batches', ['created_at'], unique=False)
    op.create_index(op.f('ix_order_batches_idempotency_key'), 'order_batches', ['idempotency_key'], unique=True)
    op.create_index('ix_order_batches_user_portfolio', 'order_batches', ['user_id', 'portfolio_id'], unique=False)
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('broker', sa.String(), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('price_limit', sa.Float(), nullable=True),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='placed'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('ext_order_id', sa.String(), nullable=True),
        sa.Column('fill_price', sa.Float(), nullable=True),
        sa.Column('fill_qty', sa.Float(), nullable=True),
        sa.Column('batch_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['batch_id'], ['order_batches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_portfolio_id'), 'orders', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_orders_broker'), 'orders', ['broker'], unique=False)
    op.create_index(op.f('ix_orders_instrument_id'), 'orders', ['instrument_id'], unique=False)
    op.create_index(op.f('ix_orders_side'), 'orders', ['side'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_created_at'), 'orders', ['created_at'], unique=False)
    op.create_index(op.f('ix_orders_ext_order_id'), 'orders', ['ext_order_id'], unique=False)
    op.create_index(op.f('ix_orders_batch_id'), 'orders', ['batch_id'], unique=False)
    op.create_index('ix_orders_portfolio_status', 'orders', ['portfolio_id', 'status'], unique=False)
    op.create_index('ix_orders_broker_status', 'orders', ['broker', 'status'], unique=False)
    
    # Create broker_connector_configs table
    op.create_table(
        'broker_connector_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('broker_name', sa.String(), nullable=False),
        sa.Column('config_json', sa.JSON(), nullable=False),
        sa.Column('active', sa.String(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_broker_connector_configs_broker_name'), 'broker_connector_configs', ['broker_name'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_broker_connector_configs_broker_name'), table_name='broker_connector_configs')
    op.drop_table('broker_connector_configs')
    
    op.drop_index('ix_orders_broker_status', table_name='orders')
    op.drop_index('ix_orders_portfolio_status', table_name='orders')
    op.drop_index(op.f('ix_orders_batch_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_ext_order_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_created_at'), table_name='orders')
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_side'), table_name='orders')
    op.drop_index(op.f('ix_orders_instrument_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_broker'), table_name='orders')
    op.drop_index(op.f('ix_orders_portfolio_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')
    
    op.drop_index('ix_order_batches_user_portfolio', table_name='order_batches')
    op.drop_index(op.f('ix_order_batches_created_at'), table_name='order_batches')
    op.drop_index(op.f('ix_order_batches_status'), table_name='order_batches')
    op.drop_index(op.f('ix_order_batches_portfolio_id'), table_name='order_batches')
    op.drop_index(op.f('ix_order_batches_user_id'), table_name='order_batches')
    op.drop_index(op.f('ix_order_batches_idempotency_key'), table_name='order_batches')
    op.drop_index(op.f('ix_order_batches_id'), table_name='order_batches')
    op.drop_table('order_batches')

