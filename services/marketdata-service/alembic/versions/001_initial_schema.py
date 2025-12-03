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
    # Create instruments table
    op.create_table(
        'instruments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('isin', sa.String(), nullable=True),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('asset_class', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=False, server_default='UTC'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_instruments_id'), 'instruments', ['id'], unique=False)
    op.create_index(op.f('ix_instruments_isin'), 'instruments', ['isin'], unique=True)
    op.create_index(op.f('ix_instruments_ticker'), 'instruments', ['ticker'], unique=False)
    op.create_index(op.f('ix_instruments_exchange'), 'instruments', ['exchange'], unique=False)
    op.create_index('ix_instruments_ticker_exchange', 'instruments', ['ticker', 'exchange'], unique=True)
    
    # Create price_points table (will be converted to TimescaleDB hypertable if available)
    op.create_table(
        'price_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('volume', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_points_id'), 'price_points', ['id'], unique=False)
    op.create_index(op.f('ix_price_points_instrument_id'), 'price_points', ['instrument_id'], unique=False)
    op.create_index(op.f('ix_price_points_timestamp'), 'price_points', ['timestamp'], unique=False)
    op.create_index('ix_price_points_instrument_timestamp', 'price_points', ['instrument_id', 'timestamp'], unique=False)
    
    # Create corporate_actions table
    op.create_table(
        'corporate_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('effective_date', sa.DateTime(), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_corporate_actions_id'), 'corporate_actions', ['id'], unique=False)
    op.create_index(op.f('ix_corporate_actions_instrument_id'), 'corporate_actions', ['instrument_id'], unique=False)
    op.create_index(op.f('ix_corporate_actions_type'), 'corporate_actions', ['type'], unique=False)
    op.create_index(op.f('ix_corporate_actions_effective_date'), 'corporate_actions', ['effective_date'], unique=False)
    op.create_index('ix_corporate_actions_instrument_effective_date', 'corporate_actions', ['instrument_id', 'effective_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_corporate_actions_instrument_effective_date', table_name='corporate_actions')
    op.drop_index(op.f('ix_corporate_actions_effective_date'), table_name='corporate_actions')
    op.drop_index(op.f('ix_corporate_actions_type'), table_name='corporate_actions')
    op.drop_index(op.f('ix_corporate_actions_instrument_id'), table_name='corporate_actions')
    op.drop_index(op.f('ix_corporate_actions_id'), table_name='corporate_actions')
    op.drop_table('corporate_actions')
    
    op.drop_index('ix_price_points_instrument_timestamp', table_name='price_points')
    op.drop_index(op.f('ix_price_points_timestamp'), table_name='price_points')
    op.drop_index(op.f('ix_price_points_instrument_id'), table_name='price_points')
    op.drop_index(op.f('ix_price_points_id'), table_name='price_points')
    op.drop_table('price_points')
    
    op.drop_index('ix_instruments_ticker_exchange', table_name='instruments')
    op.drop_index(op.f('ix_instruments_exchange'), table_name='instruments')
    op.drop_index(op.f('ix_instruments_ticker'), table_name='instruments')
    op.drop_index(op.f('ix_instruments_isin'), table_name='instruments')
    op.drop_index(op.f('ix_instruments_id'), table_name='instruments')
    op.drop_table('instruments')

