# Coding & PR Rules - Quick Reference

## ✅ All Rules Enforced

### 1. Single Responsibility ✓
- **File Limit**: < 400 LOC (enforced via pre-commit hook)
- **Function Limit**: < 80 LOC (enforced via pre-commit hook)
- **Status**: All current files comply

### 2. Type Annotations ✓
- **Requirement**: Mandatory for all public functions
- **Enforcement**: Pre-commit hook + CI check
- **Script**: `scripts/check_type_annotations.py`

### 3. Docstrings ✓
- **Requirement**: All modules and public functions
- **Format**: Google-style docstrings
- **Enforcement**: Pre-commit hook
- **Script**: `scripts/check_docstrings.py`

### 4. Test Coverage ✓
- **Requirement**: Happy path + at least one failure path
- **Enforcement**: PR review checklist
- **Example**: See any service's `tests/` directory

### 5. Dependency Injection ✓
- **Requirement**: All external services use DI
- **Pattern**: FastAPI's `Depends()`
- **Enforcement**: Code review

### 6. Structured Logging ✓
- **Requirement**: No `print()` in production code
- **Enforcement**: Pre-commit hook checks for `print(`
- **Pattern**: Use `logger.info()`, `logger.error()`, etc.

### 7. AI Agent Prompts ✓
- **Requirement**: Store in `/prompts` directory, versioned
- **Location**: `services/agent-orchestrator/prompts/v1.0.0/`
- **Enforcement**: Code review

### 8. Conventional Commits ✓
- **Requirement**: `<type>(<scope>): <description>`
- **Enforcement**: Pre-commit hook validates commit messages
- **Guide**: See `.github/COMMIT_CONVENTION.md`

### 9. CHANGELOG.md ✓
- **Requirement**: Entry for every feature delivery
- **Location**: Root `CHANGELOG.md`
- **Format**: Keep a Changelog format
- **Enforcement**: PR review

### 10. Code Diffs ✓
- **Requirement**: Unified patch format with context
- **Format**: Standard git diff format
- **Enforcement**: Code review

## Quick Commands

### Install Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

### Run All Checks
```bash
pre-commit run --all-files
```

### Run Individual Checks
```bash
# File/function size
python scripts/check_function_size.py

# Docstrings
python scripts/check_docstrings.py

# Type annotations
python scripts/check_type_annotations.py
```

### Format Code
```bash
black .
ruff check --fix .
```

## File Status

✅ All production files are under 400 LOC
✅ All functions are under 80 LOC (validated)
✅ Pre-commit hooks configured
✅ CI/CD workflows configured
✅ Documentation complete

## Next Steps

1. **Install pre-commit hooks**: `pre-commit install`
2. **Review coding standards**: `.github/CODING_STANDARDS.md`
3. **Follow commit convention**: `.github/COMMIT_CONVENTION.md`
4. **Use PR template**: `.github/pull_request_template.md`

