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
    # Create notification_templates table
    op.create_table(
        'notification_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('subject_template', sa.Text(), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_templates_id'), 'notification_templates', ['id'], unique=False)
    op.create_index(op.f('ix_notification_templates_name'), 'notification_templates', ['name'], unique=True)
    op.create_index(op.f('ix_notification_templates_channel'), 'notification_templates', ['channel'], unique=False)
    op.create_index('ix_notification_templates_name_channel', 'notification_templates', ['name', 'channel'], unique=False)
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('template_name', sa.String(), nullable=True),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_recipient'), 'notifications', ['recipient'], unique=False)
    op.create_index(op.f('ix_notifications_channel'), 'notifications', ['channel'], unique=False)
    op.create_index(op.f('ix_notifications_template_name'), 'notifications', ['template_name'], unique=False)
    op.create_index(op.f('ix_notifications_status'), 'notifications', ['status'], unique=False)
    op.create_index(op.f('ix_notifications_next_attempt_at'), 'notifications', ['next_attempt_at'], unique=False)
    op.create_index(op.f('ix_notifications_scheduled_at'), 'notifications', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index('ix_notifications_status_next_attempt', 'notifications', ['status', 'next_attempt_at'], unique=False)
    
    # Create webhook_subscriptions table
    op.create_table(
        'webhook_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('secret', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_subscriptions_event_type'), 'webhook_subscriptions', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_subscriptions_active'), 'webhook_subscriptions', ['active'], unique=False)
    op.create_index('ix_webhook_subscriptions_event_type_active', 'webhook_subscriptions', ['event_type', 'active'], unique=False)
    
    # Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_logs_id'), 'notification_logs', ['id'], unique=False)
    op.create_index(op.f('ix_notification_logs_notification_id'), 'notification_logs', ['notification_id'], unique=False)
    op.create_index(op.f('ix_notification_logs_created_at'), 'notification_logs', ['created_at'], unique=False)
    op.create_index('ix_notification_logs_notification_created', 'notification_logs', ['notification_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_notification_logs_notification_created', table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_created_at'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_notification_id'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_id'), table_name='notification_logs')
    op.drop_table('notification_logs')
    
    op.drop_index('ix_webhook_subscriptions_event_type_active', table_name='webhook_subscriptions')
    op.drop_index(op.f('ix_webhook_subscriptions_active'), table_name='webhook_subscriptions')
    op.drop_index(op.f('ix_webhook_subscriptions_event_type'), table_name='webhook_subscriptions')
    op.drop_table('webhook_subscriptions')
    
    op.drop_index('ix_notifications_status_next_attempt', table_name='notifications')
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_scheduled_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_next_attempt_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_status'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_template_name'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_channel'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_recipient'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index('ix_notification_templates_name_channel', table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_channel'), table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_name'), table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_id'), table_name='notification_templates')
    op.drop_table('notification_templates')

