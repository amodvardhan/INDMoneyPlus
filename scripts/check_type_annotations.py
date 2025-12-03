#!/usr/bin/env python3
"""Check that all public functions have type annotations"""
import ast
import sys
from pathlib import Path


def is_public(name: str) -> bool:
    """Check if a name is public (not starting with _)"""
    return not name.startswith('_')


def has_type_annotations(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function has type annotations"""
    # Check return type
    if node.returns is None:
        return False
    
    # Check all parameters have annotations (except self/cls)
    for arg in node.args.args:
        if arg.arg not in ('self', 'cls') and arg.annotation is None:
            return False
    
    return True


def check_file(file_path: Path) -> list[str]:
    """Check a single file for missing type annotations"""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_public(node.name) and not has_type_annotations(node):
                    violations.append(
                        f"{file_path}:{node.lineno}: Public function '{node.name}' missing type annotations"
                    )
    except SyntaxError as e:
        violations.append(f"{file_path}: Syntax error: {e}")
    except Exception as e:
        violations.append(f"{file_path}: Error checking file: {e}")
    
    return violations


def main():
    """Main entry point"""
    violations = []
    
    # Get files from command line or check all
    files = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if not files:
        services_dir = Path(__file__).parent.parent / "services"
        files = list(services_dir.rglob("*.py"))
        files = [str(f) for f in files if "test" not in str(f) and "__pycache__" not in str(f)]
    
    for file_path_str in files:
        file_path = Path(file_path_str)
        if file_path.suffix == '.py' and file_path.exists():
            violations.extend(check_file(file_path))
    
    if violations:
        print("Type annotation violations found:")
        for violation in violations:
            print(f"  {violation}")
        print("\nNote: This is a warning. Please add type annotations to public functions.")
        # Don't exit with error for now, just warn
        return
    
    print("All public functions have type annotations ✓")


if __name__ == "__main__":
    main()

