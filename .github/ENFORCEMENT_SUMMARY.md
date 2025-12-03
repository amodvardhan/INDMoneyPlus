# Coding & PR Rules Enforcement Summary

This document summarizes the enforcement mechanisms for coding and PR rules.

## Automated Enforcement

### Pre-commit Hooks
Location: `.pre-commit-config.yaml`

Automatically runs on every commit:
- ✅ File size check (< 400 LOC)
- ✅ Function size check (< 80 LOC)
- ✅ Docstring validation
- ✅ No console prints check
- ✅ Conventional Commits format validation
- ✅ Code formatting (Black)
- ✅ Linting (Ruff)
- ✅ Type checking (mypy)

### Installation
```bash
pip install pre-commit
pre-commit install
```

### Manual Run
```bash
pre-commit run --all-files
```

## CI/CD Enforcement

### GitHub Actions Workflow
Location: `.github/workflows/code-quality.yml`

Runs on every PR and push:
- File size validation
- Function size validation
- Docstring checks
- Print statement detection
- Type annotation checks
- Code formatting validation
- Linting validation

## Manual Validation Scripts

### Scripts Location
`scripts/` directory

### Available Scripts

1. **check_function_size.py**
   - Validates all functions are < 80 LOC
   - Usage: `python scripts/check_function_size.py [files...]`

2. **check_docstrings.py**
   - Validates all modules and public functions have docstrings
   - Usage: `python scripts/check_docstrings.py [files...]`

3. **check_type_annotations.py**
   - Validates all public functions have type annotations
   - Usage: `python scripts/check_type_annotations.py [files...]`

## PR Review Checklist

Every PR must include:
- [ ] All files < 400 LOC
- [ ] All functions < 80 LOC
- [ ] All public functions have type annotations
- [ ] All modules and public functions have docstrings
- [ ] Tests cover happy path + at least one failure path
- [ ] External services use dependency injection
- [ ] No console prints, only structured logging
- [ ] AI prompts stored in `/prompts` directory (if applicable)
- [ ] Commit messages follow Conventional Commits
- [ ] CHANGELOG.md updated

## Rule Violations

### File Size > 400 LOC
**Action**: Split file into multiple files with clear responsibilities

### Function Size > 80 LOC
**Action**: Refactor into smaller, focused functions

### Missing Type Annotations
**Action**: Add type annotations to all public function parameters and return types

### Missing Docstrings
**Action**: Add Google-style docstrings to all modules and public functions

### Console Prints
**Action**: Replace `print()` with structured logging using `logger`

### Missing Tests
**Action**: Add tests covering happy path and at least one failure path

### No Dependency Injection
**Action**: Refactor to use FastAPI's `Depends()` for external services

### AI Prompts in Code
**Action**: Move prompts to `/prompts/v<version>/` directory and load from file

### Invalid Commit Message
**Action**: Use Conventional Commits format: `<type>(<scope>): <description>`

## Examples

### ✅ Good: Properly Structured Code

```python
"""Order processing module for handling order lifecycle."""

import logging
from typing import List, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.order import Order

logger = logging.getLogger(__name__)


async def get_user_orders(
    user_id: int,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> List[Order]:
    """
    Get user orders with optional status filter.
    
    Args:
        user_id: User ID to fetch orders for
        status: Optional order status filter
        db: Database session (injected)
        
    Returns:
        List of Order objects matching criteria
        
    Raises:
        ValueError: If user_id is invalid
    """
    logger.info("Fetching user orders", extra={"user_id": user_id, "status": status})
    
    query = db.query(Order).filter(Order.user_id == user_id)
    if status:
        query = query.filter(Order.status == status)
    
    return await query.all()
```

### ❌ Bad: Violates Multiple Rules

```python
def get_orders(user_id, status):
    print(f"Getting orders for user {user_id}")
    db = Database()
    orders = db.query(Order).filter(Order.user_id == user_id)
    if status:
        orders = orders.filter(Order.status == status)
    # ... 100 more lines of code ...
    return orders
```

**Issues**:
- No type annotations
- No docstring
- Console print instead of logging
- No dependency injection
- Function likely > 80 LOC

## Getting Help

If you have questions about coding standards:
1. Check `.github/CODING_STANDARDS.md`
2. Check `.github/COMMIT_CONVENTION.md`
3. Review existing code in services for examples
4. Ask in PR review comments

