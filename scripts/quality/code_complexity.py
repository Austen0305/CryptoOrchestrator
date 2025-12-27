#!/usr/bin/env python3
"""
Code Complexity Analysis
Analyzes code complexity and identifies technical debt
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Any
import json


class ComplexityAnalyzer(ast.NodeVisitor):
    """AST-based complexity analyzer"""
    
    def __init__(self):
        self.complexity = 0
        self.functions: List[Dict[str, Any]] = []
        self.current_function = None
    
    def visit_FunctionDef(self, node):
        """Visit function definitions"""
        old_function = self.current_function
        self.current_function = {
            "name": node.name,
            "line": node.lineno,
            "complexity": 1,  # Base complexity
        }
        
        # Count decision points
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)):
                self.current_function["complexity"] += 1
            elif isinstance(child, (ast.And, ast.Or)):
                self.current_function["complexity"] += 1
        
        self.functions.append(self.current_function)
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_ClassDef(self, node):
        """Visit class definitions"""
        self.generic_visit(node)


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Python file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        analyzer = ComplexityAnalyzer()
        analyzer.visit(tree)
        
        max_complexity = max((f["complexity"] for f in analyzer.functions), default=0)
        avg_complexity = sum(f["complexity"] for f in analyzer.functions) / len(analyzer.functions) if analyzer.functions else 0
        
        return {
            "file": str(file_path),
            "functions": analyzer.functions,
            "max_complexity": max_complexity,
            "avg_complexity": round(avg_complexity, 2),
            "function_count": len(analyzer.functions),
        }
    except Exception as e:
        return {
            "file": str(file_path),
            "error": str(e),
        }


def analyze_directory(directory: Path, pattern: str = "*.py") -> List[Dict[str, Any]]:
    """Analyze all Python files in a directory"""
    results = []
    
    for file_path in directory.rglob(pattern):
        if "test" in str(file_path) or "__pycache__" in str(file_path):
            continue
        
        result = analyze_file(file_path)
        results.append(result)
    
    return results


def generate_report(results: List[Dict[str, Any]]) -> str:
    """Generate complexity report"""
    report = ["# Code Complexity Analysis Report\n\n"]
    
    # Filter out errors
    valid_results = [r for r in results if "error" not in r]
    
    if not valid_results:
        report.append("No files analyzed.\n")
        return "\n".join(report)
    
    # Overall statistics
    total_functions = sum(r["function_count"] for r in valid_results)
    max_complexity = max((r["max_complexity"] for r in valid_results), default=0)
    avg_complexity = sum(r["avg_complexity"] for r in valid_results) / len(valid_results)
    
    report.append("## Overall Statistics\n\n")
    report.append(f"- **Files Analyzed**: {len(valid_results)}\n")
    report.append(f"- **Total Functions**: {total_functions}\n")
    report.append(f"- **Max Complexity**: {max_complexity}\n")
    report.append(f"- **Average Complexity**: {avg_complexity:.2f}\n\n")
    
    # High complexity functions
    high_complexity = []
    for result in valid_results:
        for func in result["functions"]:
            if func["complexity"] > 10:
                high_complexity.append({
                    "file": result["file"],
                    "function": func["name"],
                    "complexity": func["complexity"],
                    "line": func["line"],
                })
    
    if high_complexity:
        report.append("## High Complexity Functions (>10)\n\n")
        report.append("| File | Function | Complexity | Line |\n")
        report.append("|------|----------|------------|------|\n")
        for item in sorted(high_complexity, key=lambda x: x["complexity"], reverse=True):
            report.append(f"| {item['file']} | {item['function']} | {item['complexity']} | {item['line']} |\n")
        report.append("\n")
    
    return "\n".join(report)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code complexity analysis")
    parser.add_argument("directory", help="Directory to analyze")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)
    
    results = analyze_directory(directory)
    report = generate_report(results)
    
    print(report)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()
