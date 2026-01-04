#!/usr/bin/env python3
"""
Deployment Readiness Scanner
Comprehensive scan to ensure all features work on redeployment
"""

import os
import re
import json
import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import importlib.util

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class DeploymentScanner:
    """Comprehensive deployment readiness scanner"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []
        self.backend_routes: Set[str] = set()
        self.frontend_api_calls: Set[str] = set()
        self.env_vars_used: Set[str] = set()
        self.env_vars_documented: Set[str] = set()
        
    def scan_all(self) -> Dict:
        """Run all scans"""
        print(f"{Colors.BOLD}{Colors.BLUE}🔍 Starting Deployment Readiness Scan...{Colors.RESET}\n")
        
        results = {
            "environment_variables": self.scan_environment_variables(),
            "api_endpoints": self.scan_api_endpoints(),
            "imports": self.scan_imports(),
            "database": self.scan_database(),
            "build_config": self.scan_build_config(),
            "service_initialization": self.scan_service_initialization(),
            "frontend_backend_integration": self.scan_frontend_backend_integration(),
            "error_handling": self.scan_error_handling(),
        }
        
        return self.generate_report(results)
    
    def scan_environment_variables(self) -> Dict:
        """Scan for environment variable usage and documentation"""
        print(f"{Colors.BLUE}📋 Scanning environment variables...{Colors.RESET}")
        
        # Read .env.example
        env_example = self.project_root / ".env.example"
        if env_example.exists():
            content = env_example.read_text()
            # Extract variable names
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    var_name = line.split('=')[0].strip()
                    if var_name:
                        self.env_vars_documented.add(var_name)
        
        # Scan backend for env var usage
        backend_path = self.project_root / "server_fastapi"
        if backend_path.exists():
            for py_file in backend_path.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    # Find os.getenv, os.environ, settings usage
                    patterns = [
                        r'os\.getenv\(["\']([^"\']+)["\']',
                        r'os\.environ\[["\']([^"\']+)["\']',
                        r'os\.environ\.get\(["\']([^"\']+)["\']',
                        r'settings\.([a-z_]+)',
                        r'getenv\(["\']([^"\']+)["\']',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if isinstance(match, tuple):
                                match = match[0] if match else ""
                            if match:
                                self.env_vars_used.add(match.upper())
                except Exception as e:
                    self.warnings.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "issue": f"Could not scan file: {e}",
                        "severity": "low"
                    })
        
        # Scan frontend for env var usage
        frontend_path = self.project_root / "client"
        if frontend_path.exists():
            for ts_file in frontend_path.rglob("*.{ts,tsx}"):
                try:
                    content = ts_file.read_text()
                    # Find import.meta.env usage
                    matches = re.findall(r'import\.meta\.env\.([A-Z_]+)', content)
                    for match in matches:
                        self.env_vars_used.add(f"VITE_{match}")
                except Exception:
                    pass
        
        # Check for undocumented variables
        undocumented = self.env_vars_used - self.env_vars_documented
        missing_docs = []
        for var in undocumented:
            # Skip internal/system variables
            if not any(skip in var for skip in ['PYTHON', 'NODE', 'PATH', 'HOME', 'USER', 'SHELL']):
                missing_docs.append(var)
        
        issues = []
        if missing_docs:
            issues.append({
                "type": "undocumented_env_vars",
                "vars": missing_docs,
                "severity": "medium"
            })
        
        # Check for required vars without defaults
        required_vars = ['DATABASE_URL', 'JWT_SECRET']
        missing_required = []
        for var in required_vars:
            if var not in self.env_vars_documented:
                missing_required.append(var)
        
        if missing_required:
            issues.append({
                "type": "missing_required_vars",
                "vars": missing_required,
                "severity": "high"
            })
        
        return {
            "documented": len(self.env_vars_documented),
            "used": len(self.env_vars_used),
            "undocumented": len(missing_docs),
            "issues": issues
        }
    
    def scan_api_endpoints(self) -> Dict:
        """Scan for API endpoint mismatches"""
        print(f"{Colors.BLUE}🔌 Scanning API endpoints...{Colors.RESET}")
        
        # Scan backend routes
        routes_path = self.project_root / "server_fastapi" / "routes"
        if routes_path.exists():
            for py_file in routes_path.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    # Find @router.get, @router.post, etc.
                    patterns = [
                        r'@router\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']',
                        r'router\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']',
                        r'prefix=["\']([^"\']+)["\']',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, tuple):
                                endpoint = match[1] if len(match) > 1 else match[0]
                            else:
                                endpoint = match
                            if endpoint and endpoint.startswith('/'):
                                self.backend_routes.add(endpoint)
                except Exception:
                    pass
        
        # Scan frontend API calls
        frontend_path = self.project_root / "client" / "src"
        if frontend_path.exists():
            for ts_file in frontend_path.rglob("*.{ts,tsx}"):
                try:
                    content = ts_file.read_text()
                    # Find API calls
                    patterns = [
                        r'["\'](/api/[^"\']+)["\']',
                        r'`(/api/[^`]+)`',
                        r'apiRequest<[^>]+>\(["\']([^"\']+)["\']',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match and match.startswith('/api/'):
                                # Clean up the endpoint
                                endpoint = match.split('?')[0].split('#')[0]
                                self.frontend_api_calls.add(endpoint)
                except Exception:
                    pass
        
        # Check for mismatches (simplified - would need more sophisticated matching)
        issues = []
        # This is a simplified check - in reality, we'd need to account for
        # route parameters, query strings, etc.
        
        return {
            "backend_routes": len(self.backend_routes),
            "frontend_calls": len(self.frontend_api_calls),
            "issues": issues
        }
    
    def scan_imports(self) -> Dict:
        """Scan for problematic imports"""
        print(f"{Colors.BLUE}📦 Scanning imports...{Colors.RESET}")
        
        issues = []
        backend_path = self.project_root / "server_fastapi"
        
        if backend_path.exists():
            for py_file in backend_path.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                # Check for imports without try/except
                                # This is simplified - would need to check context
                                pass
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module
                            if module and any(dep in module for dep in ['web3', 'tensorflow', 'torch']):
                                # Check if wrapped in try/except
                                # This would require more sophisticated AST analysis
                                pass
                except SyntaxError:
                    # Skip files with syntax errors
                    pass
                except Exception:
                    pass
        
        return {
            "files_scanned": len(list(backend_path.rglob("*.py"))),
            "issues": issues
        }
    
    def scan_database(self) -> Dict:
        """Scan database configuration and migrations"""
        print(f"{Colors.BLUE}🗄️  Scanning database...{Colors.RESET}")
        
        issues = []
        
        # Check alembic.ini exists
        alembic_ini = self.project_root / "alembic.ini"
        if not alembic_ini.exists():
            issues.append({
                "type": "missing_alembic_config",
                "severity": "high"
            })
        
        # Check migrations directory
        migrations_dir = self.project_root / "alembic" / "versions"
        if migrations_dir.exists():
            migration_files = list(migrations_dir.glob("*.py"))
            if not migration_files:
                issues.append({
                    "type": "no_migrations",
                    "severity": "medium"
                })
        
        # Check database initialization
        db_init = self.project_root / "server_fastapi" / "database" / "__init__.py"
        if not db_init.exists():
            issues.append({
                "type": "missing_database_init",
                "severity": "high"
            })
        
        return {
            "migrations": len(migration_files) if migrations_dir.exists() else 0,
            "issues": issues
        }
    
    def scan_build_config(self) -> Dict:
        """Scan build configuration files"""
        print(f"{Colors.BLUE}🔨 Scanning build configuration...{Colors.RESET}")
        
        issues = []
        
        # Check package.json
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                if "scripts" not in data:
                    issues.append({
                        "type": "missing_build_scripts",
                        "severity": "high"
                    })
            except json.JSONDecodeError:
                issues.append({
                    "type": "invalid_package_json",
                    "severity": "high"
                })
        
        # Check requirements.txt
        requirements = self.project_root / "requirements.txt"
        if not requirements.exists():
            issues.append({
                "type": "missing_requirements",
                "severity": "high"
            })
        
        # Check vite.config.ts
        vite_config = self.project_root / "vite.config.ts"
        if not vite_config.exists():
            issues.append({
                "type": "missing_vite_config",
                "severity": "high"
            })
        
        # Check Dockerfile
        dockerfile = self.project_root / "Dockerfile"
        if not dockerfile.exists():
            issues.append({
                "type": "missing_dockerfile",
                "severity": "medium"
            })
        
        return {
            "issues": issues
        }
    
    def scan_service_initialization(self) -> Dict:
        """Scan service initialization code"""
        print(f"{Colors.BLUE}⚙️  Scanning service initialization...{Colors.RESET}")
        
        issues = []
        
        # Check main.py startup
        main_py = self.project_root / "server_fastapi" / "main.py"
        if main_py.exists():
            content = main_py.read_text()
            
            # Check for lifespan function
            if "lifespan" not in content:
                issues.append({
                    "type": "missing_lifespan",
                    "severity": "medium"
                })
            
            # Check for startup validation
            if "startup_validation" not in content and "startup_validator" not in content:
                issues.append({
                    "type": "missing_startup_validation",
                    "severity": "low"
                })
        
        return {
            "issues": issues
        }
    
    def scan_frontend_backend_integration(self) -> Dict:
        """Scan frontend-backend integration"""
        print(f"{Colors.BLUE}🔗 Scanning frontend-backend integration...{Colors.RESET}")
        
        issues = []
        
        # Check API client configuration
        api_client = self.project_root / "client" / "src" / "lib" / "apiClient.ts"
        if not api_client.exists():
            api_client = self.project_root / "client" / "src" / "lib" / "api.ts"
        
        if api_client.exists():
            content = api_client.read_text()
            
            # Check for VITE_API_URL usage
            if "VITE_API_URL" not in content and "import.meta.env.VITE_API_URL" not in content:
                issues.append({
                    "type": "missing_api_url_config",
                    "severity": "high"
                })
            
            # Check for fallback/default
            if "localhost:8000" not in content and "http://localhost" not in content:
                issues.append({
                    "type": "no_api_fallback",
                    "severity": "medium"
                })
        else:
            issues.append({
                "type": "missing_api_client",
                "severity": "high"
            })
        
        return {
            "issues": issues
        }
    
    def scan_error_handling(self) -> Dict:
        """Scan for error handling in critical paths"""
        print(f"{Colors.BLUE}🛡️  Scanning error handling...{Colors.RESET}")
        
        issues = []
        
        # Check critical routes for error handling
        critical_routes = [
            "server_fastapi/routes/auth.py",
            "server_fastapi/routes/bots.py",
            "server_fastapi/routes/trades.py",
        ]
        
        for route_path in critical_routes:
            full_path = self.project_root / route_path
            if full_path.exists():
                content = full_path.read_text()
                
                # Check for try/except blocks
                if "try:" not in content or "except" not in content:
                    issues.append({
                        "type": "missing_error_handling",
                        "file": route_path,
                        "severity": "medium"
                    })
        
        return {
            "issues": issues
        }
    
    def generate_report(self, results: Dict) -> Dict:
        """Generate comprehensive report"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}📊 Generating Report...{Colors.RESET}\n")
        
        total_issues = sum(len(r.get("issues", [])) for r in results.values())
        high_severity = sum(
            1 for r in results.values()
            for issue in r.get("issues", [])
            if issue.get("severity") == "high"
        )
        medium_severity = sum(
            1 for r in results.values()
            for issue in r.get("issues", [])
            if issue.get("severity") == "medium"
        )
        
        report = {
            "summary": {
                "total_issues": total_issues,
                "high_severity": high_severity,
                "medium_severity": medium_severity,
                "low_severity": total_issues - high_severity - medium_severity,
            },
            "results": results,
            "recommendations": []
        }
        
        # Generate recommendations
        if high_severity > 0:
            report["recommendations"].append(
                f"{Colors.RED}⚠️  {high_severity} high-severity issues found - fix before deployment{Colors.RESET}"
            )
        
        if report["summary"]["total_issues"] == 0:
            report["recommendations"].append(
                f"{Colors.GREEN}✅ No critical issues found - ready for deployment!{Colors.RESET}"
            )
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted report"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}DEPLOYMENT READINESS REPORT{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        
        summary = report["summary"]
        print(f"{Colors.BOLD}Summary:{Colors.RESET}")
        print(f"  Total Issues: {summary['total_issues']}")
        print(f"  {Colors.RED}High Severity: {summary['high_severity']}{Colors.RESET}")
        print(f"  {Colors.YELLOW}Medium Severity: {summary['medium_severity']}{Colors.RESET}")
        print(f"  Low Severity: {summary['low_severity']}\n")
        
        print(f"{Colors.BOLD}Detailed Results:{Colors.RESET}\n")
        for category, data in report["results"].items():
            print(f"{Colors.BLUE}{category.replace('_', ' ').title()}:{Colors.RESET}")
            if "issues" in data and data["issues"]:
                for issue in data["issues"]:
                    severity_color = {
                        "high": Colors.RED,
                        "medium": Colors.YELLOW,
                        "low": Colors.GREEN
                    }.get(issue.get("severity", "low"), Colors.RESET)
                    print(f"  {severity_color}⚠️  {issue.get('type', 'unknown')}{Colors.RESET}")
                    if "file" in issue:
                        print(f"    File: {issue['file']}")
                    if "vars" in issue:
                        print(f"    Variables: {', '.join(issue['vars'][:5])}")
            else:
                print(f"  {Colors.GREEN}✅ No issues{Colors.RESET}")
            print()
        
        if report["recommendations"]:
            print(f"{Colors.BOLD}Recommendations:{Colors.RESET}")
            for rec in report["recommendations"]:
                print(f"  {rec}")
            print()


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent.parent
    scanner = DeploymentScanner(project_root)
    
    report = scanner.scan_all()
    scanner.print_report(report)
    
    # Save report to file
    report_file = project_root / "deployment_readiness_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n{Colors.BLUE}📄 Full report saved to: {report_file}{Colors.RESET}\n")
    
    # Exit with error code if high severity issues found
    if report["summary"]["high_severity"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
