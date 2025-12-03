# Auth Service

Production-ready authentication and user management microservice with JWT-based authentication, refresh tokens, rate limiting, and audit logging.

## Features

- **User Registration & Authentication**: Secure user registration and login with password hashing
- **JWT Tokens**: Access tokens (1 hour) and refresh tokens (7 days) with JTI tracking
- **Token Revocation**: Refresh token revocation on logout and refresh
- **Rate Limiting**: Redis-based rate limiting for login attempts (5 attempts per 5 minutes)
- **RBAC**: Basic role-based access control with `is_superuser` flag
- **Audit Logging**: Comprehensive audit trail for all authentication actions
- **Observability**: Prometheus metrics endpoint and health checks

## Database Models

- **User**: `id`, `email`, `hashed_password`, `is_active`, `is_superuser`, `created_at`
- **RefreshToken**: `id`, `user_id`, `token_jti`, `expires_at`, `revoked_at`
- **AuditLog**: `id`, `user_id`, `action`, `ip`, `user_agent`, `metadata`, `created_at`

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register a new user
  - Request: `{email: string, password: string}`
  - Response: `201 UserRead`
  
- `POST /api/v1/auth/login` - Login and get tokens
  - Request: `{email: string, password: string}`
  - Response: `200 {access_token, refresh_token, token_type}`
  
- `POST /api/v1/auth/refresh` - Refresh access token
  - Request: `{refresh_token: string}`
  - Response: `200 {access_token, refresh_token, token_type}`
  
- `POST /api/v1/auth/logout` - Logout and revoke refresh token
  - Request: `{refresh_token: string}`
  - Response: `204 No Content`
  
- `GET /api/v1/auth/me` - Get current user (requires Bearer token)
  - Response: `200 UserRead`

### User Management (Admin Only)

- `GET /api/v1/users` - List all users (requires superuser)
  - Query params: `skip` (default: 0), `limit` (default: 100, max: 1000)
  - Response: `200 [UserRead]`

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
poetry run uvicorn app.main:app --reload --port 8001
```

### Using Docker Compose

```bash
cd services/auth-service
docker-compose -f docker-compose.dev.yml up --build
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Auth service on port 8001

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string (asyncpg driver)
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Secret key for JWT signing (use strong random key in production)
- `JWT_ACCESS_TOKEN_EXPIRATION`: Access token expiration in seconds (default: 3600)
- `JWT_REFRESH_TOKEN_EXPIRATION`: Refresh token expiration in seconds (default: 604800)
- `RATE_LIMIT_LOGIN_ATTEMPTS`: Max login attempts before rate limiting (default: 5)
- `RATE_LIMIT_WINDOW_SECONDS`: Rate limit window in seconds (default: 300)

## Testing

### Run All Tests

```bash
poetry run pytest -v
```

### Run Tests with Coverage

```bash
poetry run pytest -v --cov=app --cov-report=html
```

### Run Specific Test File

```bash
poetry run pytest tests/test_auth.py -v
```

### Test Categories

- **test_auth.py**: Registration, login, refresh, logout, token validation
- **test_users.py**: Admin user listing, RBAC checks
- **test_rate_limit.py**: Rate limiting functionality

## Manual Verification Steps

### 1. Register a New User

```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```

**Expected**: `201 Created` with user data (no password)

### 2. Login

```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```

**Expected**: `200 OK` with `access_token` and `refresh_token`

### 3. Get Current User

```bash
# Save token from login response
TOKEN="your_access_token_here"

curl -X GET http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected**: `200 OK` with user information

### 4. Refresh Token

```bash
# Save refresh_token from login response
REFRESH_TOKEN="your_refresh_token_here"

curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```

**Expected**: `200 OK` with new `access_token` and `refresh_token`

### 5. Logout

```bash
curl -X POST http://localhost:8001/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```

**Expected**: `204 No Content`

### 6. Verify Token Revocation

After logout, try to refresh with the same refresh token:

```bash
curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```

**Expected**: `401 Unauthorized` with "revoked" message

### 7. Rate Limiting

Make 6 failed login attempts:

```bash
for i in {1..6}; do
  curl -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "wrongpassword"}'
  echo ""
done
```

**Expected**: First 5 attempts return `401`, 6th attempt returns `429 Too Many Requests`

### 8. Admin User Listing

First, create a superuser in the database:

```sql
UPDATE users SET is_superuser = true WHERE email = 'test@example.com';
```

Then login and list users:

```bash
# Login as superuser
LOGIN_RESPONSE=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}')

ADMIN_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# List users
curl -X GET "http://localhost:8001/api/v1/users?skip=0&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected**: `200 OK` with array of users

### 9. Health Check

```bash
curl http://localhost:8001/health
```

**Expected**: `200 OK` with `{"status": "healthy", "service": "auth-service", "version": "0.1.0"}`

### 10. Metrics

```bash
curl http://localhost:8001/metrics
```

**Expected**: `200 OK` with Prometheus metrics format

## Acceptance Criteria

✅ **Registration**
- [x] User can register with email and password (min 8 chars)
- [x] Duplicate email registration returns 400
- [x] Password is hashed with bcrypt
- [x] User is created with `is_active=True`, `is_superuser=False`
- [x] Audit log entry created for registration

✅ **Login**
- [x] User can login with correct credentials
- [x] Returns access token (1 hour) and refresh token (7 days)
- [x] Refresh token stored in database with JTI
- [x] Invalid credentials return 401
- [x] Inactive users cannot login (403)
- [x] Rate limiting after 5 failed attempts (429)
- [x] Rate limit resets on successful login
- [x] Audit log entries for login attempts

✅ **Token Refresh**
- [x] User can refresh access token with valid refresh token
- [x] New tokens issued, old refresh token revoked
- [x] Revoked tokens cannot be used (401)
- [x] Expired tokens cannot be used (401)
- [x] Invalid tokens return 401

✅ **Logout**
- [x] Refresh token is revoked on logout
- [x] Revoked token cannot be used for refresh
- [x] Audit log entry created

✅ **Current User**
- [x] User can get their own info with valid access token
- [x] Invalid/missing token returns 401
- [x] Inactive users cannot access (403)

✅ **Admin Features**
- [x] Superusers can list all users
- [x] Regular users cannot list users (403)
- [x] Pagination support (skip/limit)

✅ **Security**
- [x] Passwords never returned in responses
- [x] JWT tokens signed with secret key
- [x] Refresh tokens tracked with JTI
- [x] Token revocation implemented
- [x] Rate limiting on login

✅ **Observability**
- [x] Health check endpoint
- [x] Prometheus metrics endpoint
- [x] Audit logging for all auth actions
- [x] Request metadata captured (IP, user agent)

✅ **Database**
- [x] Alembic migrations for all tables
- [x] Foreign key constraints
- [x] Indexes on frequently queried fields
- [x] Cascade deletes for refresh tokens

✅ **Testing**
- [x] Unit tests for all endpoints
- [x] Integration tests with test database
- [x] Rate limiting tests
- [x] Token revocation tests
- [x] RBAC tests

✅ **DevOps**
- [x] Dockerfile for containerization
- [x] docker-compose.dev.yml with Postgres + Redis
- [x] CI/CD workflow (lint, test, build)
- [x] .env.example with all configuration

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
