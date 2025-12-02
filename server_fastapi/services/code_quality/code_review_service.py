"""
Code Review Service - Automated code quality analysis and review suggestions.

This service provides automated code review capabilities including:
- Code complexity analysis
- Performance issue detection
- Security vulnerability scanning
- Best practice validation
- Documentation completeness checking
"""

import ast
import os
import re
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class IssueSeverity(Enum):
    """Severity levels for code review issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class CodeIssue:
    """Represents a code review issue."""
    file_path: str
    line_number: int
    severity: IssueSeverity
    category: str
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

class CodeReviewService:
    """Service for automated code review and quality analysis."""
    
    def __init__(self, project_root: str):
        """Initialize code review service.
        
        Args:
            project_root: Root directory of the project to analyze
        """
        self.project_root = Path(project_root)
        self.issues: List[CodeIssue] = []
        
    def analyze_file(self, file_path: str) -> List[CodeIssue]:
        """Analyze a single Python file for code quality issues.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            List of code issues found
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST
            try:
                tree = ast.parse(content)
                issues.extend(self._analyze_ast(file_path, tree, content))
            except SyntaxError as e:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=e.lineno or 0,
                    severity=IssueSeverity.ERROR,
                    category="syntax",
                    message=f"Syntax error: {e.msg}",
                    suggestion="Fix the syntax error before proceeding"
                ))
                
            # Text-based checks
            issues.extend(self._check_documentation(file_path, content))
            issues.extend(self._check_security(file_path, content))
            issues.extend(self._check_best_practices(file_path, content))
            
        except Exception as e:
            issues.append(CodeIssue(
                file_path=file_path,
                line_number=0,
                severity=IssueSeverity.ERROR,
                category="file_read",
                message=f"Error reading file: {str(e)}"
            ))
            
        return issues
    
    def _analyze_ast(self, file_path: str, tree: ast.AST, content: str) -> List[CodeIssue]:
        """Analyze AST for code quality issues."""
        issues = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            # Check function complexity
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 15:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=IssueSeverity.WARNING,
                        category="complexity",
                        message=f"Function '{node.name}' has high complexity ({complexity})",
                        suggestion="Consider breaking this function into smaller functions"
                    ))
                
                # Check missing docstrings
                if not ast.get_docstring(node):
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=IssueSeverity.INFO,
                        category="documentation",
                        message=f"Function '{node.name}' is missing a docstring",
                        suggestion="Add a docstring explaining the function's purpose, args, and return value"
                    ))
            
            # Check class documentation
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=IssueSeverity.INFO,
                        category="documentation",
                        message=f"Class '{node.name}' is missing a docstring",
                        suggestion="Add a docstring explaining the class's purpose"
                    ))
            
            # Check for bare except clauses
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=IssueSeverity.WARNING,
                        category="exception_handling",
                        message="Bare 'except:' clause found",
                        suggestion="Specify the exception type or use 'except Exception:'"
                    ))
            
            # Check for print statements (should use logging)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=IssueSeverity.INFO,
                        category="best_practice",
                        message="Using print() instead of logging",
                        suggestion="Use logging.info(), logging.debug(), etc. instead"
                    ))
                    
        return issues
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
                
        return complexity
    
    def _check_documentation(self, file_path: str, content: str) -> List[CodeIssue]:
        """Check for documentation issues."""
        issues = []
        lines = content.split('\n')
        
        # Check for TODO comments
        for i, line in enumerate(lines, 1):
            if 'TODO' in line or 'FIXME' in line:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    severity=IssueSeverity.INFO,
                    category="todo",
                    message="TODO or FIXME comment found",
                    code_snippet=line.strip()
                ))
                
        return issues
    
    def _check_security(self, file_path: str, content: str) -> List[CodeIssue]:
        """Check for security issues."""
        issues = []
        lines = content.split('\n')
        
        # Check for hardcoded secrets patterns
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Potential hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Potential hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Potential hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Potential hardcoded token"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, message in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Ignore if it's in a comment or uses environment variable
                    if '#' not in line and 'os.getenv' not in line and 'os.environ' not in line:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=i,
                            severity=IssueSeverity.CRITICAL,
                            category="security",
                            message=message,
                            suggestion="Use environment variables or a secrets manager"
                        ))
                        
        # Check for SQL injection risks
        sql_patterns = [
            r'execute\([^)]*%s',
            r'execute\([^)]*\+',
            r'execute\([^)]*f["\']',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line):
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=i,
                        severity=IssueSeverity.ERROR,
                        category="security",
                        message="Potential SQL injection vulnerability",
                        suggestion="Use parameterized queries with placeholders"
                    ))
                    
        return issues
    
    def _check_best_practices(self, file_path: str, content: str) -> List[CodeIssue]:
        """Check for best practice violations."""
        issues = []
        lines = content.split('\n')
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    severity=IssueSeverity.INFO,
                    category="style",
                    message=f"Line too long ({len(line)} characters)",
                    suggestion="Break line into multiple lines or refactor"
                ))
        
        # Check for import organization
        import_lines = [i for i, line in enumerate(lines) if line.strip().startswith('import ') or line.strip().startswith('from ')]
        if import_lines:
            # Check if imports are not at the top
            first_code_line = next((i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""')), 0)
            if import_lines[0] > first_code_line + 10:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=import_lines[0] + 1,
                    severity=IssueSeverity.INFO,
                    category="style",
                    message="Imports should be at the top of the file",
                    suggestion="Move all imports to the top of the file"
                ))
                
        return issues
    
    def analyze_directory(self, directory: str = None, extensions: List[str] = None) -> Dict[str, Any]:
        """Analyze all Python files in a directory.
        
        Args:
            directory: Directory to analyze (default: project_root)
            extensions: File extensions to analyze (default: ['.py'])
            
        Returns:
            Summary of analysis results
        """
        if directory is None:
            directory = self.project_root
        else:
            directory = Path(directory)
            
        if extensions is None:
            extensions = ['.py']
            
        all_issues = []
        files_analyzed = 0
        
        for ext in extensions:
            for file_path in directory.rglob(f'*{ext}'):
                # Skip virtual environments and cache directories
                if any(part in file_path.parts for part in ['venv', 'env', '__pycache__', 'node_modules', '.git']):
                    continue
                    
                issues = self.analyze_file(str(file_path))
                all_issues.extend(issues)
                files_analyzed += 1
                
        # Categorize issues
        by_severity = {}
        by_category = {}
        
        for issue in all_issues:
            # Group by severity
            sev = issue.severity.value
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(issue)
            
            # Group by category
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)
            
        return {
            'files_analyzed': files_analyzed,
            'total_issues': len(all_issues),
            'by_severity': {k: len(v) for k, v in by_severity.items()},
            'by_category': {k: len(v) for k, v in by_category.items()},
            'issues': all_issues,
            'summary': self._generate_summary(all_issues, files_analyzed)
        }
    
    def _generate_summary(self, issues: List[CodeIssue], files_analyzed: int) -> str:
        """Generate a human-readable summary of issues."""
        if not issues:
            return f"✅ No issues found in {files_analyzed} files analyzed!"
            
        summary_lines = [
            f"📊 Code Review Summary ({files_analyzed} files analyzed)",
            f"Total Issues: {len(issues)}",
            ""
        ]
        
        # Group by severity
        by_sev = {}
        for issue in issues:
            sev = issue.severity.value
            by_sev[sev] = by_sev.get(sev, 0) + 1
            
        if by_sev.get('critical', 0) > 0:
            summary_lines.append(f"🔴 Critical: {by_sev['critical']}")
        if by_sev.get('error', 0) > 0:
            summary_lines.append(f"❌ Errors: {by_sev['error']}")
        if by_sev.get('warning', 0) > 0:
            summary_lines.append(f"⚠️  Warnings: {by_sev['warning']}")
        if by_sev.get('info', 0) > 0:
            summary_lines.append(f"ℹ️  Info: {by_sev['info']}")
            
        return '\n'.join(summary_lines)
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate a detailed code review report.
        
        Args:
            output_file: Optional file path to save the report
            
        Returns:
            Report content as string
        """
        results = self.analyze_directory()
        
        report_lines = [
            "# Code Review Report",
            f"Generated: {__import__('datetime').datetime.now().isoformat()}",
            "",
            results['summary'],
            "",
            "## Issues by Category",
            ""
        ]
        
        # Group issues by category
        by_category = {}
        for issue in results['issues']:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)
            
        for category, issues in sorted(by_category.items()):
            report_lines.append(f"### {category.replace('_', ' ').title()} ({len(issues)} issues)")
            report_lines.append("")
            
            for issue in issues[:10]:  # Show first 10 per category
                report_lines.append(f"- **{issue.file_path}:{issue.line_number}** - {issue.message}")
                if issue.suggestion:
                    report_lines.append(f"  - 💡 Suggestion: {issue.suggestion}")
                    
            if len(issues) > 10:
                report_lines.append(f"  - ... and {len(issues) - 10} more")
                
            report_lines.append("")
            
        report_content = '\n'.join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
        return report_content


# CLI usage
if __name__ == '__main__':
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else '.'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'code_review_report.md'
    
    reviewer = CodeReviewService(project_root)
    report = reviewer.generate_report(output_file)
    
    print(report)
    print(f"\nReport saved to: {output_file}")
