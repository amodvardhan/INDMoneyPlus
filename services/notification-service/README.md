# Notification Service

Centralized notification hub for email, SMS, push notifications, and webhooks. Supports templates, scheduling (cron-like), retries with exponential backoff, and webhook subscriptions for third parties.

## Features

- **Multi-Channel Support**: Email, SMS, and Push notifications
- **Template Engine**: Template-based notifications with variable substitution
- **Scheduling**: Cron-like scheduling for future notifications
- **Retry Logic**: Exponential backoff retry mechanism with configurable attempts
- **Background Worker**: Redis-based queue processing
- **Webhook Subscriptions**: Subscribe to notification events
- **Event Ingestion**: Endpoint for internal services to publish events
- **Pluggable Transports**: Support for SendGrid, Twilio, Firebase, and in-memory transports

## Database Models

- **NotificationTemplate**: `id`, `name`, `channel`, `subject_template`, `body_template`, `created_at`, `updated_at`
- **Notification**: `id`, `recipient`, `channel`, `template_name`, `payload_json`, `status`, `attempts`, `next_attempt_at`, `scheduled_at`, `created_at`, `sent_at`
- **WebhookSubscription**: `id`, `url`, `event_type`, `secret`, `active`, `created_at`, `updated_at`
- **NotificationLog**: `id`, `notification_id`, `channel`, `response_code`, `response_body`, `created_at`

## API Endpoints

### Notifications

- `POST /api/v1/notifications/notify` - Enqueue a notification
  - Request: `{"channel": "email|sms|push", "recipient": "...", "template_name": "...", "payload": {...}, "scheduled_at": "..."}`
  - Response: `NotificationResponse` with notification_id and status

- `GET /api/v1/notifications/{id}/logs` - Get logs for a notification
  - Response: Array of `NotificationLogRead`

### Webhooks

- `POST /api/v1/webhooks/subscribe` - Subscribe to webhook events
  - Request: `{"url": "...", "event_type": "...", "secret": "..."}`
  - Response: `WebhookSubscriptionRead`

- `GET /api/v1/webhooks/subscriptions` - List all webhook subscriptions
- `DELETE /api/v1/webhooks/subscriptions/{id}` - Delete a webhook subscription

### Events

- `POST /api/v1/events/ingest` - Ingest event from internal services
  - Request: `{"event_type": "...", "payload": {...}}`
  - Response: Delivery status

### Health & Metrics

- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

## Running Locally

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL 15+
- Redis 7+

### Setup

1. **Install dependencies:**
```bash
poetry install
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run database migrations:**
```bash
poetry run alembic upgrade head
```

4. **Start the service:**
```bash
poetry run uvicorn app.main:app --reload --port 8007
```

### Using Docker Compose

```bash
cd services/notification-service
docker-compose -f docker-compose.dev.yml up --build
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Notification service on port 8007

## Template Engine

Templates use `{{variable}}` syntax for variable substitution:

**Example Template:**
```
Subject: Welcome {{name}}!
Body: Hello {{name}}, your verification code is {{code}}.
```

**Usage:**
```json
{
  "template_name": "welcome_email",
  "payload": {
    "name": "John Doe",
    "code": "12345"
  }
}
```

## Transport Configuration

### In-Memory (Default)

In-memory transports store notifications in memory for development/testing:
- `EMAIL_TRANSPORT_TYPE=in_memory`
- `SMS_TRANSPORT_TYPE=in_memory`
- `PUSH_TRANSPORT_TYPE=in_memory`

### SendGrid (Email)

```bash
EMAIL_TRANSPORT_TYPE=sendgrid
SENDGRID_API_KEY=your-api-key
SENDGRID_FROM_EMAIL=noreply@example.com
```

### Twilio (SMS)

```bash
SMS_TRANSPORT_TYPE=twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
```

### Firebase (Push)

```bash
PUSH_TRANSPORT_TYPE=firebase
FIREBASE_CREDENTIALS_PATH=/path/to/credentials.json
```

## Background Worker

The background worker processes notifications from the Redis queue:
- Polls for pending notifications
- Processes in batches (configurable)
- Implements exponential backoff retry
- Logs all attempts

**Configuration:**
- `WORKER_ENABLED=true` - Enable/disable worker
- `WORKER_BATCH_SIZE=10` - Notifications per batch
- `WORKER_POLL_INTERVAL=1.0` - Poll interval in seconds
- `MAX_RETRY_ATTEMPTS=3` - Maximum retry attempts
- `RETRY_BACKOFF_BASE=2.0` - Exponential backoff base

## Testing

### Run All Tests

```bash
poetry run pytest -v
```

### Run Tests with Coverage

```bash
poetry run pytest -v --cov=app --cov-report=html
```

### Test Categories

- **test_notifications.py**: Notification endpoint tests
- **test_transports.py**: Transport implementation tests

## Manual Verification Steps

### 1. Send a Notification

```bash
curl -X POST "http://localhost:8007/api/v1/notifications/notify" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "recipient": "test@example.com",
    "payload": {
      "subject": "Test Alert",
      "body": "This is a test notification"
    }
  }'
```

**Expected**: `200 OK` with notification_id and status "pending"

### 2. Check Notification Logs

```bash
# Get notification_id from step 1
curl "http://localhost:8007/api/v1/notifications/{notification_id}/logs"
```

**Expected**: `200 OK` with array of log entries showing:
- Response code (200 for success)
- Response body
- Timestamp

### 3. Create a Template

```sql
INSERT INTO notification_templates (name, channel, subject_template, body_template)
VALUES (
  'alert_template',
  'email',
  'Alert: {{alert_type}}',
  'You have a new {{alert_type}} alert: {{message}}'
);
```

### 4. Send Notification with Template

```bash
curl -X POST "http://localhost:8007/api/v1/notifications/notify" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "recipient": "test@example.com",
    "template_name": "alert_template",
    "payload": {
      "alert_type": "Security",
      "message": "Unusual login detected"
    }
  }'
```

### 5. Subscribe to Webhook

```bash
curl -X POST "http://localhost:8007/api/v1/webhooks/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "event_type": "notification.sent",
    "secret": "webhook-secret-key"
  }'
```

### 6. Ingest Event

```bash
curl -X POST "http://localhost:8007/api/v1/events/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "notification.sent",
    "payload": {
      "notification_id": 123,
      "channel": "email"
    }
  }'
```

**Expected**: Webhook subscribers receive the event

### 7. Health Check

```bash
curl http://localhost:8007/health
```

**Expected**: `200 OK` with service status

### 8. Metrics

```bash
curl http://localhost:8007/metrics
```

**Expected**: `200 OK` with Prometheus metrics format

## Acceptance Criteria

✅ **Database Models**
- [x] NotificationTemplate model with templates
- [x] Notification model with status tracking
- [x] WebhookSubscription model
- [x] NotificationLog model for audit trail

✅ **Transport System**
- [x] Pluggable transport interfaces
- [x] In-memory implementations (email, SMS, push)
- [x] SendGrid email transport interface
- [x] Twilio SMS transport interface
- [x] Firebase push transport interface

✅ **Template Engine**
- [x] Variable substitution with {{variable}} syntax
- [x] Support for subject and body templates

✅ **Background Worker**
- [x] Redis-based queue processing
- [x] Batch processing
- [x] Exponential backoff retry
- [x] Configurable retry attempts

✅ **Notification Endpoints**
- [x] POST /api/v1/notifications/notify
- [x] GET /api/v1/notifications/{id}/logs
- [x] Template support
- [x] Scheduling support

✅ **Webhook System**
- [x] Webhook subscription endpoint
- [x] Event delivery to subscribers
- [x] Signature verification support
- [x] Event ingestion endpoint

✅ **Observability**
- [x] Health check endpoint
- [x] Prometheus metrics endpoint
- [x] Notification logs for audit

✅ **Testing**
- [x] Unit tests for transports
- [x] Integration tests for endpoints
- [x] Tests for template rendering

✅ **DevOps**
- [x] Dockerfile for containerization
- [x] docker-compose.dev.yml with Postgres + Redis
- [x] .env.example
- [x] Alembic migrations
- [x] CI/CD workflow

## Sample Notification Log Entry

After sending a notification, you can retrieve logs:

```json
{
  "id": 1,
  "notification_id": 123,
  "channel": "email",
  "response_code": 200,
  "response_body": "Email queued for test@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

## Development

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy app
```

### Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

## License

[Your License Here]

