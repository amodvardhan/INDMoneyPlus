# Conventional Commits

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

## Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files

## Scope

The scope should be the name of the service or module affected:
- `auth`: Auth Service
- `marketdata`: Market Data Service
- `aggregator`: Aggregator Service
- `agent-orchestrator`: Agent Orchestrator Service
- `notification`: Notification Service
- `order-orchestrator`: Order Orchestrator Service
- `shared`: Shared code across services

## Examples

### Feature
```
feat(auth): add JWT refresh token endpoint
feat(marketdata): implement WebSocket price streaming
feat(order-orchestrator): add order batching support
```

### Bug Fix
```
fix(auth): handle expired refresh tokens correctly
fix(marketdata): fix price data caching issue
fix(aggregator): resolve CSV parsing edge case
```

### Documentation
```
docs(api): update order endpoint documentation
docs(readme): add setup instructions for notification service
```

### Refactoring
```
refactor(orders): split large order processing function
refactor(auth): extract token validation logic
```

### Testing
```
test(auth): add tests for refresh token rotation
test(notifications): add failure path tests for email transport
```

### Chore
```
chore(deps): update FastAPI to 0.104.0
chore(ci): add code quality checks workflow
```

## Breaking Changes

If your commit introduces a breaking change, add `!` after the type/scope:

```
feat(api)!: change order endpoint response format
```

Or add `BREAKING CHANGE:` in the footer:

```
feat(api): update order endpoint

BREAKING CHANGE: Order response now includes additional fields
```

## Multi-line Commits

For complex changes, use a multi-line commit:

```
feat(order-orchestrator): add reconciliation endpoint

- Implement reconciliation report generation
- Add P&L calculation logic
- Include order statistics in report

Closes #123
```

## Pre-commit Hook

A pre-commit hook automatically validates commit messages. To bypass (not recommended):

```bash
git commit --no-verify -m "message"
```

