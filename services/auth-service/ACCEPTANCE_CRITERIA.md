# Auth Service - Acceptance Criteria & Test Commands

## ✅ All Requirements Met

### Database Models
- ✅ **User**: `id`, `email`, `hashed_password`, `is_active`, `is_superuser`, `created_at`
- ✅ **RefreshToken**: `id`, `user_id`, `token_jti`, `expires_at`, `revoked_at`
- ✅ **AuditLog**: `id`, `user_id`, `action`, `ip`, `user_agent`, `metadata`, `created_at`

### Endpoints Implemented
- ✅ `POST /api/v1/auth/register` - Register new user
- ✅ `POST /api/v1/auth/login` - Login with rate limiting
- ✅ `POST /api/v1/auth/refresh` - Refresh tokens with revocation
- ✅ `POST /api/v1/auth/logout` - Logout with token revocation
- ✅ `GET /api/v1/auth/me` - Get current user (requires token)
- ✅ `GET /api/v1/users` - List users (admin-only, requires superuser)
- ✅ `GET /health` - Health check
- ✅ `GET /metrics` - Prometheus metrics

### Features
- ✅ JWT access tokens (1 hour expiration)
- ✅ JWT refresh tokens (7 days expiration) with JTI tracking
- ✅ Token revocation on logout and refresh
- ✅ Rate limiting (5 attempts per 5 minutes) using Redis
- ✅ RBAC with `is_superuser` flag
- ✅ Audit logging for all auth actions
- ✅ Prometheus metrics endpoint
- ✅ Alembic migrations

## Test Commands

### 1. Run All Tests
```bash
cd services/auth-service
poetry run pytest -v
```

### 2. Run Tests with Coverage
```bash
poetry run pytest -v --cov=app --cov-report=html
```

### 3. Run Specific Test Suite
```bash
# Authentication tests
poetry run pytest tests/test_auth.py -v

# User management tests
poetry run pytest tests/test_users.py -v

# Rate limiting tests
poetry run pytest tests/test_rate_limit.py -v
```

## Manual Verification Commands

### Prerequisites
```bash
# Start services
cd services/auth-service
docker-compose -f docker-compose.dev.yml up -d

# Or run locally
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8001
```

### 1. Register User
```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```
**Expected**: `201 Created` with user data

### 2. Login
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```
**Expected**: `200 OK` with `access_token` and `refresh_token`

### 3. Get Current User
```bash
TOKEN="<access_token_from_login>"
curl -X GET http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```
**Expected**: `200 OK` with user information

### 4. Refresh Token
```bash
REFRESH_TOKEN="<refresh_token_from_login>"
curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```
**Expected**: `200 OK` with new tokens

### 5. Logout
```bash
curl -X POST http://localhost:8001/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```
**Expected**: `204 No Content`

### 6. Verify Token Revocation
```bash
# Try to refresh with revoked token
curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```
**Expected**: `401 Unauthorized` with "revoked" message

### 7. Test Rate Limiting
```bash
# Make 6 failed login attempts
for i in {1..6}; do
  curl -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "wrongpassword"}'
  echo ""
done
```
**Expected**: First 5 return `401`, 6th returns `429`

### 8. Admin User Listing
```bash
# First, make user a superuser in database
# Then login and list users
ADMIN_TOKEN="<admin_access_token>"
curl -X GET "http://localhost:8001/api/v1/users?skip=0&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```
**Expected**: `200 OK` with array of users

### 9. Health Check
```bash
curl http://localhost:8001/health
```
**Expected**: `200 OK` with service status

### 10. Metrics
```bash
curl http://localhost:8001/metrics
```
**Expected**: `200 OK` with Prometheus format

## Acceptance Criteria Checklist

### Registration ✅
- [x] User can register with email and password (min 8 chars)
- [x] Duplicate email returns 400
- [x] Password hashed with bcrypt
- [x] User created with `is_active=True`, `is_superuser=False`
- [x] Audit log entry created

### Login ✅
- [x] User can login with correct credentials
- [x] Returns access token (1 hour) and refresh token (7 days)
- [x] Refresh token stored with JTI
- [x] Invalid credentials return 401
- [x] Inactive users cannot login (403)
- [x] Rate limiting after 5 failed attempts (429)
- [x] Rate limit resets on successful login
- [x] Audit log entries created

### Token Refresh ✅
- [x] User can refresh access token
- [x] New tokens issued, old refresh token revoked
- [x] Revoked tokens cannot be used (401)
- [x] Expired tokens cannot be used (401)
- [x] Invalid tokens return 401

### Logout ✅
- [x] Refresh token revoked on logout
- [x] Revoked token cannot be used for refresh
- [x] Audit log entry created

### Current User ✅
- [x] User can get their info with valid token
- [x] Invalid/missing token returns 401
- [x] Inactive users cannot access (403)

### Admin Features ✅
- [x] Superusers can list all users
- [x] Regular users cannot list users (403)
- [x] Pagination support (skip/limit)

### Security ✅
- [x] Passwords never returned
- [x] JWT tokens signed with secret
- [x] Refresh tokens tracked with JTI
- [x] Token revocation implemented
- [x] Rate limiting on login

### Observability ✅
- [x] Health check endpoint
- [x] Prometheus metrics endpoint
- [x] Audit logging for all actions
- [x] Request metadata captured

### Database ✅
- [x] Alembic migrations for all tables
- [x] Foreign key constraints
- [x] Indexes on frequently queried fields
- [x] Cascade deletes

### Testing ✅
- [x] Unit tests for all endpoints
- [x] Integration tests with test database
- [x] Rate limiting tests
- [x] Token revocation tests
- [x] RBAC tests

### DevOps ✅
- [x] Dockerfile
- [x] docker-compose.dev.yml with Postgres + Redis
- [x] CI/CD workflow (lint, test, build)
- [x] .env.example

## Files Delivered

### Core Application
- `app/main.py` - FastAPI application with lifespan management
- `app/core/config.py` - Configuration with environment variables
- `app/core/database.py` - Database connection and session management
- `app/core/security.py` - JWT token generation, password hashing
- `app/core/rate_limit.py` - Redis-based rate limiting
- `app/core/audit.py` - Audit logging utilities
- `app/core/dependencies.py` - FastAPI dependencies (auth, RBAC)

### Models & Schemas
- `app/models/user.py` - SQLAlchemy models (User, RefreshToken, AuditLog)
- `app/schemas/user.py` - Pydantic schemas for request/response

### API Endpoints
- `app/api/auth.py` - Authentication endpoints (register, login, refresh, logout, me)
- `app/api/users.py` - User management endpoints (admin-only)

### Database Migrations
- `alembic/env.py` - Alembic environment configuration
- `alembic/versions/001_initial_schema.py` - Initial database schema migration

### Tests
- `tests/conftest.py` - Pytest fixtures and test configuration
- `tests/test_auth.py` - Authentication endpoint tests
- `tests/test_users.py` - User management endpoint tests
- `tests/test_rate_limit.py` - Rate limiting tests

### DevOps
- `Dockerfile` - Container image definition
- `docker-compose.dev.yml` - Local development environment
- `.github/workflows/auth-service-ci.yml` - CI/CD pipeline
- `.env.example` - Environment variable template

### Documentation
- `README.md` - Comprehensive service documentation
- `ACCEPTANCE_CRITERIA.md` - This file

## Next Steps

1. **Run tests**: `poetry run pytest -v`
2. **Start services**: `docker-compose -f docker-compose.dev.yml up`
3. **Verify endpoints**: Use the manual verification commands above
4. **Review code**: Check all files for any customizations needed
5. **Deploy**: Use the CI/CD pipeline or deploy manually

