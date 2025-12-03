# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive coding standards and PR rules enforcement
- Pre-commit hooks for automated code quality checks
- File size validation scripts (400 LOC limit)
- Function size validation scripts (80 LOC limit)
- Docstring validation scripts
- Type annotation validation scripts
- Conventional Commits validation
- PR template with coding standards checklist
- Code quality GitHub Actions workflow
- AI agent prompt versioning system under `/prompts` directory
- CHANGELOG.md for tracking all project changes
- Order Orchestrator Service with batching, idempotency, and broker routing
- Notification Service with multi-channel support (email, SMS, push) and webhook subscriptions
- Agent Orchestrator Service with LangChain integration and three agent flows (Analysis, Rebalance, Execution-Prep)
- Aggregator Service for multi-custodian holdings aggregation with CSV parsing and reconciliation
- Market Data Service with TimescaleDB support and pluggable adapter interface
- Auth Service with JWT tokens, refresh tokens, and RBAC support
- Comprehensive coding standards and PR rules documentation
- Pre-commit hooks for automated code quality checks
- CHANGELOG.md for tracking all changes

### Changed
- Enforced coding standards: file size limits (400 LOC), function size limits (80 LOC)
- Mandatory type annotations for all public functions
- Required docstrings for all modules and public functions
- Structured logging replaces all console prints
- Dependency injection pattern for all external services

### Fixed
- Improved error handling across all services
- Enhanced test coverage with happy path and failure path tests

## [0.1.0] - 2024-01-01

### Added
- Initial project structure
- Service architecture with FastAPI microservices
- Docker and Docker Compose configurations
- CI/CD workflows with GitHub Actions
- Database migrations with Alembic
- Prometheus metrics and health check endpoints

