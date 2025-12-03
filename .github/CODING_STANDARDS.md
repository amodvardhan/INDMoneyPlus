# Coding Standards & PR Rules

This document outlines the coding standards and PR rules for the INDMoney++ project.

## 1. Single Responsibility Principle

### File Size Limit
- **Maximum 400 lines of code (LOC) per file**
- If a file exceeds 400 LOC, split it into multiple files with clear responsibilities

### Function Size Limit
- **Maximum 80 lines of code (LOC) per function**
- If a function exceeds 80 LOC, refactor into smaller, focused functions

### Example
```python
# ❌ Bad: 150 LOC function
def process_order(order_data, user_data, payment_data, inventory_data):
    # 150 lines of code...
    pass

# ✅ Good: Split into focused functions
def validate_order(order_data: OrderData) -> ValidationResult:
    """Validate order data"""
    # 30 lines
    pass

def process_payment(payment_data: PaymentData) -> PaymentResult:
    """Process payment"""
    # 40 lines
    pass

def update_inventory(inventory_data: InventoryData) -> None:
    """Update inventory"""
    # 25 lines
    pass
```

## 2. Type Annotations

### Mandatory Type Annotations
- **All public functions must have type annotations**
- Include parameter types, return types, and optional types
- Use `typing` module for complex types (List, Dict, Optional, etc.)

### Example
```python
# ❌ Bad: No type annotations
def get_user_orders(user_id, status):
    return db.query(Order).filter(...)

# ✅ Good: Full type annotations
from typing import List, Optional
from app.models.order import Order

def get_user_orders(user_id: int, status: Optional[str] = None) -> List[Order]:
    """Get user orders with optional status filter"""
    return db.query(Order).filter(...)
```

## 3. Docstrings

### Module Docstrings
- **Every module must have a docstring** describing its purpose

### Function Docstrings
- **All public functions must have docstrings**
- Use Google-style docstrings
- Include: description, Args, Returns, Raises (if applicable)

### Example
```python
"""Order processing module for handling order lifecycle."""

from typing import List, Optional

def process_order_batch(
    orders: List[Order],
    user_id: int,
    portfolio_id: int
) -> OrderBatch:
    """
    Process a batch of orders for a user portfolio.
    
    Args:
        orders: List of Order objects to process
        user_id: User ID who owns the orders
        portfolio_id: Portfolio ID for the orders
        
    Returns:
        OrderBatch object containing processed orders
        
    Raises:
        ValidationError: If any order fails validation
        InsufficientFundsError: If user has insufficient funds
    """
    # Implementation
    pass
```

## 4. Test Coverage

### Test Requirements
- **Every feature must have tests covering:**
  - Happy path (successful execution)
  - At least one failure path (error handling)

### Example
```python
# tests/test_orders.py
import pytest
from app.api.orders import create_order

@pytest.mark.asyncio
async def test_create_order_success(client: AsyncClient):
    """Test successful order creation (happy path)"""
    response = await client.post("/api/v1/orders", json={...})
    assert response.status_code == 200
    assert "order_id" in response.json()

@pytest.mark.asyncio
async def test_create_order_validation_failure(client: AsyncClient):
    """Test order creation with invalid data (failure path)"""
    response = await client.post("/api/v1/orders", json={"invalid": "data"})
    assert response.status_code == 400
    assert "validation" in response.json()["detail"].lower()
```

## 5. Dependency Injection

### External Services
- **All external services must use dependency injection**
- This enables easy mocking in tests
- Use FastAPI's `Depends()` for dependency injection

### Example
```python
# ❌ Bad: Direct instantiation
def process_order(order_data):
    db = Database()  # Hard to mock
    email_service = EmailService()  # Hard to mock
    # ...

# ✅ Good: Dependency injection
from fastapi import Depends
from app.core.database import get_db
from app.core.email import get_email_service

async def process_order(
    order_data: OrderData,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    """Process order with injected dependencies"""
    # Easy to mock in tests
    pass
```

## 6. Structured Logging

### No Console Prints
- **No `print()` statements in production code**
- Use structured logging with appropriate log levels

### Example
```python
# ❌ Bad: Console prints
def process_order(order):
    print(f"Processing order {order.id}")
    print(f"Order status: {order.status}")

# ✅ Good: Structured logging
import logging

logger = logging.getLogger(__name__)

def process_order(order: Order) -> None:
    """Process an order"""
    logger.info("Processing order", extra={
        "order_id": order.id,
        "order_status": order.status,
        "user_id": order.user_id
    })
    
    try:
        # Process order
        logger.debug("Order processing started", extra={"order_id": order.id})
    except Exception as e:
        logger.error("Order processing failed", extra={
            "order_id": order.id,
            "error": str(e)
        }, exc_info=True)
```

## 7. AI Agent Prompts

### Prompt Storage
- **All AI agent prompts must be stored under `/prompts` directory**
- Version prompts with semantic versioning
- Use descriptive filenames

### Example Structure
```
services/agent-orchestrator/
  prompts/
    v1.0.0/
      analysis_flow_system_prompt.txt
      rebalance_flow_system_prompt.txt
      execution_prep_prompt.txt
    v1.1.0/
      analysis_flow_system_prompt.txt  # Updated version
```

### Code Usage
```python
# ❌ Bad: Hardcoded prompt
def analyze_portfolio(portfolio_id: int) -> str:
    prompt = "Analyze this portfolio and provide insights..."
    # ...

# ✅ Good: Load from file
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "v1.0.0"

def analyze_portfolio(portfolio_id: int) -> str:
    """Analyze portfolio using versioned prompt"""
    prompt_path = PROMPTS_DIR / "analysis_flow_system_prompt.txt"
    prompt = prompt_path.read_text()
    # ...
```

## 8. Conventional Commits

### Commit Message Format
- **All commits must follow Conventional Commits format**
- Format: `<type>(<scope>): <description>`

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(auth): add JWT refresh token endpoint
fix(marketdata): handle missing price data gracefully
docs(api): update API documentation for orders endpoint
refactor(orders): split large order processing function
test(notifications): add tests for email transport
chore(deps): update FastAPI to 0.104.0
```

## 9. CHANGELOG.md

### Changelog Entry Format
- **Every feature delivery must include a CHANGELOG.md entry**
- Use [Keep a Changelog](https://keepachangelog.com/) format
- Group by version and change type

### Example
```markdown
# Changelog

## [Unreleased]

### Added
- Order Orchestrator Service with batching and idempotency support
- Broker connector interfaces for Zerodha and Alpaca
- Reconciliation endpoint with P&L calculations

### Changed
- Updated order validation to include margin checks

### Fixed
- Fixed idempotency key handling for duplicate requests

## [0.1.0] - 2024-01-01

### Added
- Initial release of Auth Service
- Initial release of Market Data Service
```

## 10. Code Diff Format

### Unified Patch Format
- **When returning code diffs, use unified patch format**
- Include file paths and clear context
- Show line numbers and changes clearly

### Example
```diff
--- a/services/order-orchestrator/app/api/orders.py
+++ b/services/order-orchestrator/app/api/orders.py
@@ -45,6 +45,12 @@ async def create_order_batch(
     batch: OrderBatchCreate,
     db: AsyncSession = Depends(get_db),
 ):
+    """
+    Create an order batch with validation and routing.
+    
+    Args:
+        batch: Order batch creation request
+        db: Database session
+    """
     # Validate orders
     for order in batch.orders:
         validate_order(order)
```

## Enforcement

### Pre-commit Hooks
- Use pre-commit hooks to enforce these rules automatically
- See `.pre-commit-config.yaml` for configuration

### Code Review Checklist
- [ ] All files < 400 LOC
- [ ] All functions < 80 LOC
- [ ] All public functions have type annotations
- [ ] All modules and public functions have docstrings
- [ ] Tests cover happy path + at least one failure path
- [ ] External services use dependency injection
- [ ] No console prints, only structured logging
- [ ] AI prompts stored in `/prompts` directory
- [ ] Commit message follows Conventional Commits
- [ ] CHANGELOG.md updated

## Tools

### Linting & Formatting
- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **mypy**: Static type checking

### Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting

### Pre-commit
- **pre-commit**: Git hooks framework

