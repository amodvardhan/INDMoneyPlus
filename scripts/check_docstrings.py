#!/usr/bin/env python3
"""Check that all modules and public functions have docstrings"""
import ast
import sys
from pathlib import Path


def is_public(name: str) -> bool:
    """Check if a name is public (not starting with _)"""
    return not name.startswith('_')


def check_file(file_path: Path) -> list[str]:
    """Check a single file for missing docstrings"""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filename=str(file_path))
        
        # Check module docstring
        if not ast.get_docstring(tree):
            violations.append(f"{file_path}:1: Module missing docstring")
        
        # Check functions and classes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_public(node.name) and not ast.get_docstring(node):
                    violations.append(
                        f"{file_path}:{node.lineno}: Public function '{node.name}' missing docstring"
                    )
            elif isinstance(node, ast.ClassDef):
                if is_public(node.name) and not ast.get_docstring(node):
                    violations.append(
                        f"{file_path}:{node.lineno}: Public class '{node.name}' missing docstring"
                    )
    except SyntaxError as e:
        violations.append(f"{file_path}: Syntax error: {e}")
    except Exception as e:
        violations.append(f"{file_path}: Error checking file: {e}")
    
    return violations


def main():
    """Main entry point"""
    violations = []
    
    # Get files from pre-commit
    files = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if not files:
        # If no files provided, check all Python files in services
        services_dir = Path(__file__).parent.parent / "services"
        files = list(services_dir.rglob("*.py"))
        files = [str(f) for f in files if "test" not in str(f) and "__pycache__" not in str(f)]
    
    for file_path_str in files:
        file_path = Path(file_path_str)
        if file_path.suffix == '.py' and file_path.exists():
            violations.extend(check_file(file_path))
    
    if violations:
        print("Docstring violations found:")
        for violation in violations:
            print(f"  {violation}")
        sys.exit(1)
    
    print("All modules and public functions have docstrings ✓")


if __name__ == "__main__":
    main()

