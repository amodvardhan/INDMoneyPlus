#!/usr/bin/env python3
"""Check that all functions are under 80 LOC"""
import ast
import sys
from pathlib import Path


def get_function_lines(node: ast.FunctionDef, source_lines: list[str]) -> int:
    """Calculate lines of code for a function"""
    start_line = node.lineno - 1
    end_line = node.end_lineno - 1 if hasattr(node, 'end_lineno') else start_line
    
    # Count non-empty, non-comment lines
    loc = 0
    for i in range(start_line, end_line + 1):
        line = source_lines[i].strip()
        if line and not line.startswith('#'):
            loc += 1
    
    return loc


def check_file(file_path: Path) -> list[str]:
    """Check a single file for function size violations"""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.split('\n')
        
        tree = ast.parse(source, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                loc = get_function_lines(node, source_lines)
                if loc > 80:
                    violations.append(
                        f"{file_path}:{node.lineno}: Function '{node.name}' has {loc} LOC "
                        f"(exceeds 80 LOC limit)"
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
        print("Function size violations found:")
        for violation in violations:
            print(f"  {violation}")
        sys.exit(1)
    
    print("All functions are within 80 LOC limit ✓")


if __name__ == "__main__":
    main()

