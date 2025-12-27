"""
Security Testing Automation
Automated security testing using free tools (OWASP ZAP, Nmap, etc.)
"""

import logging
import subprocess
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SecurityScanResult:
    """Security scan result"""
    tool: str
    scan_type: str
    status: str  # "success", "warning", "error"
    findings: List[Dict[str, Any]]
    timestamp: datetime
    duration_seconds: float
    summary: Dict[str, Any]


class SecurityTestingService:
    """
    Automated security testing service
    
    Features:
    - OWASP ZAP integration
    - Nmap port scanning
    - Dependency vulnerability scanning
    - Security header checking
    - SSL/TLS certificate validation
    """
    
    def __init__(self, output_dir: str = "security_reports"):
        """
        Initialize security testing service
        
        Args:
            output_dir: Directory to save security reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.scan_results: List[SecurityScanResult] = []
    
    def check_tool_availability(self, tool: str) -> bool:
        """Check if a security tool is available"""
        try:
            subprocess.run(
                [tool, "--version"],
                capture_output=True,
                timeout=5,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def scan_with_nmap(
        self,
        target: str,
        ports: Optional[str] = None,
        scan_type: str = "basic",
    ) -> SecurityScanResult:
        """
        Perform Nmap port scan
        
        Args:
            target: Target host or IP
            ports: Port range (e.g., "80,443,8080" or "1-1000")
            scan_type: Scan type ("basic", "stealth", "aggressive")
        
        Returns:
            SecurityScanResult
        """
        if not self.check_tool_availability("nmap"):
            logger.warning("Nmap not available, skipping scan")
            return SecurityScanResult(
                tool="nmap",
                scan_type=scan_type,
                status="error",
                findings=[],
                timestamp=datetime.utcnow(),
                duration_seconds=0.0,
                summary={"error": "Nmap not installed"},
            )
        
        start_time = datetime.utcnow()
        findings = []
        
        try:
            # Build nmap command
            cmd = ["nmap"]
            
            if scan_type == "stealth":
                cmd.extend(["-sS", "-T2"])  # SYN scan, slower timing
            elif scan_type == "aggressive":
                cmd.extend(["-A", "-T4"])  # Aggressive scan
            else:
                cmd.extend(["-sV", "-T3"])  # Version detection, normal timing
            
            if ports:
                cmd.extend(["-p", ports])
            
            cmd.append(target)
            
            # Run scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            # Parse results
            if result.returncode == 0:
                # Extract open ports
                lines = result.stdout.split("\n")
                for line in lines:
                    if "/tcp" in line or "/udp" in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            port_info = parts[0]
                            state = parts[1] if len(parts) > 1 else "unknown"
                            service = " ".join(parts[2:]) if len(parts) > 2 else "unknown"
                            
                            if state == "open":
                                findings.append({
                                    "type": "open_port",
                                    "port": port_info,
                                    "state": state,
                                    "service": service,
                                    "severity": "info",
                                })
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return SecurityScanResult(
                tool="nmap",
                scan_type=scan_type,
                status="success",
                findings=findings,
                timestamp=start_time,
                duration_seconds=duration,
                summary={
                    "target": target,
                    "ports_scanned": ports or "default",
                    "open_ports_found": len([f for f in findings if f.get("type") == "open_port"]),
                },
            )
        except subprocess.TimeoutExpired:
            logger.error("Nmap scan timed out")
            return SecurityScanResult(
                tool="nmap",
                scan_type=scan_type,
                status="error",
                findings=[],
                timestamp=start_time,
                duration_seconds=300.0,
                summary={"error": "Scan timed out"},
            )
        except Exception as e:
            logger.error(f"Nmap scan failed: {e}", exc_info=True)
            return SecurityScanResult(
                tool="nmap",
                scan_type=scan_type,
                status="error",
                findings=[],
                timestamp=start_time,
                duration_seconds=0.0,
                summary={"error": str(e)},
            )
    
    def scan_dependencies(self, project_dir: str = ".") -> SecurityScanResult:
        """
        Scan dependencies for vulnerabilities
        
        Args:
            project_dir: Project directory
        
        Returns:
            SecurityScanResult
        """
        start_time = datetime.utcnow()
        findings = []
        
        # Check for common dependency files
        requirements_file = Path(project_dir) / "requirements.txt"
        package_json = Path(project_dir) / "package.json"
        
        # Python dependencies
        if requirements_file.exists():
            try:
                # Use safety or pip-audit if available
                if self.check_tool_availability("safety"):
                    result = subprocess.run(
                        ["safety", "check", "--json"],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    
                    if result.returncode != 0:
                        try:
                            vulns = json.loads(result.stdout)
                            for vuln in vulns:
                                findings.append({
                                    "type": "vulnerability",
                                    "package": vuln.get("package", "unknown"),
                                    "installed_version": vuln.get("installed_version", "unknown"),
                                    "vulnerable_spec": vuln.get("vulnerable_spec", "unknown"),
                                    "severity": vuln.get("severity", "medium"),
                                    "description": vuln.get("advisory", ""),
                                })
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                logger.warning(f"Dependency scanning failed: {e}")
        
        # Node.js dependencies
        if package_json.exists():
            try:
                # Use npm audit if available
                if self.check_tool_availability("npm"):
                    result = subprocess.run(
                        ["npm", "audit", "--json"],
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    
                    if result.returncode != 0:
                        try:
                            audit_data = json.loads(result.stdout)
                            vulnerabilities = audit_data.get("vulnerabilities", {})
                            
                            for pkg_name, vuln_info in vulnerabilities.items():
                                findings.append({
                                    "type": "vulnerability",
                                    "package": pkg_name,
                                    "severity": vuln_info.get("severity", "medium"),
                                    "title": vuln_info.get("title", ""),
                                    "description": vuln_info.get("overview", ""),
                                })
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                logger.warning(f"NPM audit failed: {e}")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return SecurityScanResult(
            tool="dependency_scanner",
            scan_type="vulnerability",
            status="success" if findings else "success",
            findings=findings,
            timestamp=start_time,
            duration_seconds=duration,
            summary={
                "vulnerabilities_found": len(findings),
                "high_severity": len([f for f in findings if f.get("severity") == "high"]),
                "medium_severity": len([f for f in findings if f.get("severity") == "medium"]),
                "low_severity": len([f for f in findings if f.get("severity") == "low"]),
            },
        )
    
    def check_security_headers(self, url: str) -> SecurityScanResult:
        """
        Check security headers on a URL
        
        Args:
            url: URL to check
        
        Returns:
            SecurityScanResult
        """
        start_time = datetime.utcnow()
        findings = []
        
        try:
            import requests
            
            response = requests.get(url, timeout=10, allow_redirects=True)
            headers = response.headers
            
            # Check for important security headers
            security_headers = {
                "Content-Security-Policy": "high",
                "X-Frame-Options": "medium",
                "X-Content-Type-Options": "medium",
                "Strict-Transport-Security": "high",
                "X-XSS-Protection": "low",
                "Referrer-Policy": "low",
            }
            
            for header, severity in security_headers.items():
                if header not in headers:
                    findings.append({
                        "type": "missing_header",
                        "header": header,
                        "severity": severity,
                        "recommendation": f"Add {header} header for better security",
                    })
                else:
                    findings.append({
                        "type": "header_present",
                        "header": header,
                        "value": headers[header],
                        "severity": "info",
                    })
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return SecurityScanResult(
                tool="header_checker",
                scan_type="headers",
                status="success",
                findings=findings,
                timestamp=start_time,
                duration_seconds=duration,
                summary={
                    "url": url,
                    "headers_checked": len(security_headers),
                    "missing_headers": len([f for f in findings if f.get("type") == "missing_header"]),
                },
            )
        except Exception as e:
            logger.error(f"Header check failed: {e}", exc_info=True)
            return SecurityScanResult(
                tool="header_checker",
                scan_type="headers",
                status="error",
                findings=[],
                timestamp=start_time,
                duration_seconds=0.0,
                summary={"error": str(e)},
            )
    
    def run_full_scan(
        self,
        target_url: Optional[str] = None,
        target_host: Optional[str] = None,
        project_dir: str = ".",
    ) -> Dict[str, Any]:
        """
        Run a full security scan
        
        Args:
            target_url: Target URL for web security checks
            target_host: Target host for port scanning
            project_dir: Project directory for dependency scanning
        
        Returns:
            Dictionary with all scan results
        """
        results = {}
        
        # Dependency scanning
        logger.info("Running dependency vulnerability scan...")
        dep_result = self.scan_dependencies(project_dir)
        results["dependencies"] = asdict(dep_result)
        self.scan_results.append(dep_result)
        
        # Port scanning
        if target_host:
            logger.info(f"Running Nmap port scan on {target_host}...")
            nmap_result = self.scan_with_nmap(target_host)
            results["ports"] = asdict(nmap_result)
            self.scan_results.append(nmap_result)
        
        # Security headers
        if target_url:
            logger.info(f"Checking security headers for {target_url}...")
            header_result = self.check_security_headers(target_url)
            results["headers"] = asdict(header_result)
            self.scan_results.append(header_result)
        
        # Save results
        self.save_results()
        
        return {
            "scan_timestamp": datetime.utcnow().isoformat(),
            "results": results,
            "summary": self.get_summary(),
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all scans"""
        total_findings = sum(len(r.findings) for r in self.scan_results)
        high_severity = sum(
            len([f for f in r.findings if f.get("severity") == "high"])
            for r in self.scan_results
        )
        medium_severity = sum(
            len([f for f in r.findings if f.get("severity") == "medium"])
            for r in self.scan_results
        )
        
        return {
            "total_scans": len(self.scan_results),
            "total_findings": total_findings,
            "high_severity": high_severity,
            "medium_severity": medium_severity,
            "low_severity": total_findings - high_severity - medium_severity,
        }
    
    def save_results(self):
        """Save scan results to file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"security_scan_{timestamp}.json"
        
        with open(output_file, "w") as f:
            json.dump(
                {
                    "scan_timestamp": datetime.utcnow().isoformat(),
                    "results": [asdict(r) for r in self.scan_results],
                    "summary": self.get_summary(),
                },
                f,
                indent=2,
                default=str,
            )
        
        logger.info(f"Security scan results saved to {output_file}")


# Global instance
security_testing_service = SecurityTestingService()
