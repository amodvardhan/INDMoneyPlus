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
    # Create broker_accounts table
    op.create_table(
        'broker_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('broker_name', sa.String(), nullable=False),
        sa.Column('external_account_id', sa.String(), nullable=False),
        sa.Column('account_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_broker_accounts_id'), 'broker_accounts', ['id'], unique=False)
    op.create_index(op.f('ix_broker_accounts_user_id'), 'broker_accounts', ['user_id'], unique=False)
    op.create_index(op.f('ix_broker_accounts_broker_name'), 'broker_accounts', ['broker_name'], unique=False)
    op.create_index('ix_broker_accounts_user_broker', 'broker_accounts', ['user_id', 'broker_name'], unique=False)
    op.create_index('ix_broker_accounts_external_id', 'broker_accounts', ['external_account_id'], unique=False)
    
    # Create raw_statements table
    op.create_table(
        'raw_statements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('statement_hash', sa.String(), nullable=False),
        sa.Column('ingested_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], ['broker_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_statements_id'), 'raw_statements', ['id'], unique=False)
    op.create_index(op.f('ix_raw_statements_account_id'), 'raw_statements', ['account_id'], unique=False)
    op.create_index(op.f('ix_raw_statements_statement_hash'), 'raw_statements', ['statement_hash'], unique=True)
    op.create_index(op.f('ix_raw_statements_ingested_at'), 'raw_statements', ['ingested_at'], unique=False)
    
    # Create normalized_holdings table
    op.create_table(
        'normalized_holdings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=True),
        sa.Column('isin', sa.String(), nullable=True),
        sa.Column('ticker', sa.String(), nullable=True),
        sa.Column('exchange', sa.String(), nullable=True),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('avg_price', sa.Float(), nullable=True),
        sa.Column('valuation', sa.Float(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], ['broker_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_normalized_holdings_id'), 'normalized_holdings', ['id'], unique=False)
    op.create_index(op.f('ix_normalized_holdings_account_id'), 'normalized_holdings', ['account_id'], unique=False)
    op.create_index(op.f('ix_normalized_holdings_instrument_id'), 'normalized_holdings', ['instrument_id'], unique=False)
    op.create_index(op.f('ix_normalized_holdings_isin'), 'normalized_holdings', ['isin'], unique=False)
    op.create_index(op.f('ix_normalized_holdings_ticker'), 'normalized_holdings', ['ticker'], unique=False)
    op.create_index(op.f('ix_normalized_holdings_updated_at'), 'normalized_holdings', ['updated_at'], unique=False)
    op.create_index('ix_normalized_holdings_account_instrument', 'normalized_holdings', ['account_id', 'instrument_id'], unique=False)
    op.create_index('ix_normalized_holdings_account_updated', 'normalized_holdings', ['account_id', 'updated_at'], unique=False)
    
    # Create reconciliation_exceptions table
    op.create_table(
        'reconciliation_exceptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['broker_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliation_exceptions_id'), 'reconciliation_exceptions', ['id'], unique=False)
    op.create_index(op.f('ix_reconciliation_exceptions_account_id'), 'reconciliation_exceptions', ['account_id'], unique=False)
    op.create_index(op.f('ix_reconciliation_exceptions_resolved'), 'reconciliation_exceptions', ['resolved'], unique=False)
    op.create_index(op.f('ix_reconciliation_exceptions_created_at'), 'reconciliation_exceptions', ['created_at'], unique=False)
    
    # Create instrument_mappings table
    op.create_table(
        'instrument_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('isin', sa.String(), nullable=True),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=True),
        sa.Column('broker_variant', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_instrument_mappings_id'), 'instrument_mappings', ['id'], unique=False)
    op.create_index(op.f('ix_instrument_mappings_isin'), 'instrument_mappings', ['isin'], unique=False)
    op.create_index(op.f('ix_instrument_mappings_ticker'), 'instrument_mappings', ['ticker'], unique=False)
    op.create_index(op.f('ix_instrument_mappings_exchange'), 'instrument_mappings', ['exchange'], unique=False)
    op.create_index('ix_instrument_mappings_ticker_exchange', 'instrument_mappings', ['ticker', 'exchange'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_instrument_mappings_ticker_exchange', table_name='instrument_mappings')
    op.drop_index(op.f('ix_instrument_mappings_exchange'), table_name='instrument_mappings')
    op.drop_index(op.f('ix_instrument_mappings_ticker'), table_name='instrument_mappings')
    op.drop_index(op.f('ix_instrument_mappings_isin'), table_name='instrument_mappings')
    op.drop_index(op.f('ix_instrument_mappings_id'), table_name='instrument_mappings')
    op.drop_table('instrument_mappings')
    
    op.drop_index(op.f('ix_reconciliation_exceptions_created_at'), table_name='reconciliation_exceptions')
    op.drop_index(op.f('ix_reconciliation_exceptions_resolved'), table_name='reconciliation_exceptions')
    op.drop_index(op.f('ix_reconciliation_exceptions_account_id'), table_name='reconciliation_exceptions')
    op.drop_index(op.f('ix_reconciliation_exceptions_id'), table_name='reconciliation_exceptions')
    op.drop_table('reconciliation_exceptions')
    
    op.drop_index('ix_normalized_holdings_account_updated', table_name='normalized_holdings')
    op.drop_index('ix_normalized_holdings_account_instrument', table_name='normalized_holdings')
    op.drop_index(op.f('ix_normalized_holdings_updated_at'), table_name='normalized_holdings')
    op.drop_index(op.f('ix_normalized_holdings_ticker'), table_name='normalized_holdings')
    op.drop_index(op.f('ix_normalized_holdings_isin'), table_name='normalized_holdings')
    op.drop_index(op.f('ix_normalized_holdings_instrument_id'), table_name='normalized_holdings')
    op.drop_index(op.f('ix_normalized_holdings_account_id'), table_name='normalized_holdings')
    op.drop_index(op.f('ix_normalized_holdings_id'), table_name='normalized_holdings')
    op.drop_table('normalized_holdings')
    
    op.drop_index(op.f('ix_raw_statements_ingested_at'), table_name='raw_statements')
    op.drop_index(op.f('ix_raw_statements_statement_hash'), table_name='raw_statements')
    op.drop_index(op.f('ix_raw_statements_account_id'), table_name='raw_statements')
    op.drop_index(op.f('ix_raw_statements_id'), table_name='raw_statements')
    op.drop_table('raw_statements')
    
    op.drop_index('ix_broker_accounts_external_id', table_name='broker_accounts')
    op.drop_index('ix_broker_accounts_user_broker', table_name='broker_accounts')
    op.drop_index(op.f('ix_broker_accounts_broker_name'), table_name='broker_accounts')
    op.drop_index(op.f('ix_broker_accounts_user_id'), table_name='broker_accounts')
    op.drop_index(op.f('ix_broker_accounts_id'), table_name='broker_accounts')
    op.drop_table('broker_accounts')

