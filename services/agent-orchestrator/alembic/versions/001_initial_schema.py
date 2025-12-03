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
    # Create agent_runs table
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('flow_type', sa.String(), nullable=False),
        sa.Column('input_json', sa.JSON(), nullable=False),
        sa.Column('output_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='running'),
        sa.Column('executed_by', sa.Integer(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_runs_id'), 'agent_runs', ['id'], unique=False)
    op.create_index(op.f('ix_agent_runs_user_id'), 'agent_runs', ['user_id'], unique=False)
    op.create_index(op.f('ix_agent_runs_flow_type'), 'agent_runs', ['flow_type'], unique=False)
    op.create_index(op.f('ix_agent_runs_status'), 'agent_runs', ['status'], unique=False)
    op.create_index(op.f('ix_agent_runs_created_at'), 'agent_runs', ['created_at'], unique=False)
    op.create_index('ix_agent_runs_user_flow', 'agent_runs', ['user_id', 'flow_type'], unique=False)
    
    # Create agent_action_logs table
    op.create_table(
        'agent_action_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_run_id', sa.Integer(), nullable=False),
        sa.Column('step', sa.Integer(), nullable=False),
        sa.Column('tool_called', sa.String(), nullable=False),
        sa.Column('tool_input', sa.JSON(), nullable=True),
        sa.Column('tool_output', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_action_logs_id'), 'agent_action_logs', ['id'], unique=False)
    op.create_index(op.f('ix_agent_action_logs_agent_run_id'), 'agent_action_logs', ['agent_run_id'], unique=False)
    op.create_index(op.f('ix_agent_action_logs_tool_called'), 'agent_action_logs', ['tool_called'], unique=False)
    op.create_index(op.f('ix_agent_action_logs_timestamp'), 'agent_action_logs', ['timestamp'], unique=False)
    op.create_index('ix_agent_action_logs_run_step', 'agent_action_logs', ['agent_run_id', 'step'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_agent_action_logs_run_step', table_name='agent_action_logs')
    op.drop_index(op.f('ix_agent_action_logs_timestamp'), table_name='agent_action_logs')
    op.drop_index(op.f('ix_agent_action_logs_tool_called'), table_name='agent_action_logs')
    op.drop_index(op.f('ix_agent_action_logs_agent_run_id'), table_name='agent_action_logs')
    op.drop_index(op.f('ix_agent_action_logs_id'), table_name='agent_action_logs')
    op.drop_table('agent_action_logs')
    
    op.drop_index('ix_agent_runs_user_flow', table_name='agent_runs')
    op.drop_index(op.f('ix_agent_runs_created_at'), table_name='agent_runs')
    op.drop_index(op.f('ix_agent_runs_status'), table_name='agent_runs')
    op.drop_index(op.f('ix_agent_runs_flow_type'), table_name='agent_runs')
    op.drop_index(op.f('ix_agent_runs_user_id'), table_name='agent_runs')
    op.drop_index(op.f('ix_agent_runs_id'), table_name='agent_runs')
    op.drop_table('agent_runs')

