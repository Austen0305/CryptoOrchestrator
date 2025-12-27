#!/usr/bin/env python3
"""
Log Aggregator and Analyzer
Aggregates logs from multiple sources and provides analysis.
"""

import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter, defaultdict
import sys

class LogAggregator:
    """Aggregate and analyze logs from multiple sources."""
    
    def __init__(self, log_dirs: List[str] = None):
        self.log_dirs = log_dirs or ["logs", "server_fastapi/logs", "."]
        self.log_patterns = {
            "error": re.compile(r"ERROR|error|Error|FAILED|failed|Failed|Exception", re.IGNORECASE),
            "warning": re.compile(r"WARNING|warning|Warning|WARN|warn", re.IGNORECASE),
            "info": re.compile(r"INFO|info|Info", re.IGNORECASE),
            "timestamp": re.compile(r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})"),
            "http_status": re.compile(r"HTTP\s+(\d{3})|\s(\d{3})\s"),
            "endpoint": re.compile(r"(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-]+)"),
        }
        
        self.logs = []
        self.stats = {
            "total_lines": 0,
            "errors": 0,
            "warnings": 0,
            "info": 0,
            "by_level": Counter(),
            "by_hour": defaultdict(int),
            "by_endpoint": Counter(),
            "error_patterns": Counter(),
            "http_status_codes": Counter()
        }
    
    def find_log_files(self) -> List[Path]:
        """Find all log files in specified directories."""
        log_files = []
        
        for log_dir in self.log_dirs:
            dir_path = Path(log_dir)
            if not dir_path.exists():
                continue
            
            # Find .log files
            log_files.extend(dir_path.glob("*.log"))
            log_files.extend(dir_path.glob("**/*.log"))
        
        return sorted(set(log_files))
    
    def parse_log_line(self, line: str, source: str) -> Optional[Dict]:
        """Parse a single log line."""
        if not line.strip():
            return None
        
        log_entry = {
            "raw": line,
            "source": source,
            "timestamp": None,
            "level": "unknown",
            "endpoint": None,
            "http_status": None
        }
        
        # Extract timestamp
        timestamp_match = self.log_patterns["timestamp"].search(line)
        if timestamp_match:
            try:
                log_entry["timestamp"] = datetime.fromisoformat(timestamp_match.group(1).replace(' ', 'T'))
            except:
                pass
        
        # Determine log level
        if self.log_patterns["error"].search(line):
            log_entry["level"] = "error"
        elif self.log_patterns["warning"].search(line):
            log_entry["level"] = "warning"
        elif self.log_patterns["info"].search(line):
            log_entry["level"] = "info"
        
        # Extract endpoint
        endpoint_match = self.log_patterns["endpoint"].search(line)
        if endpoint_match:
            log_entry["endpoint"] = f"{endpoint_match.group(1)} {endpoint_match.group(2)}"
        
        # Extract HTTP status code
        status_match = self.log_patterns["http_status"].search(line)
        if status_match:
            log_entry["http_status"] = status_match.group(1) or status_match.group(2)
        
        return log_entry
    
    def aggregate_logs(self, hours: Optional[int] = None):
        """Aggregate logs from all sources."""
        print("🔍 Finding log files...")
        log_files = self.find_log_files()
        
        if not log_files:
            print("⚠️  No log files found")
            return
        
        print(f"Found {len(log_files)} log file(s)")
        
        cutoff_time = None
        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            print(f"Filtering logs from last {hours} hour(s)")
        
        for log_file in log_files:
            print(f"  Reading: {log_file}")
            
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        self.stats["total_lines"] += 1
                        
                        log_entry = self.parse_log_line(line, str(log_file))
                        if not log_entry:
                            continue
                        
                        # Filter by time if specified
                        if cutoff_time and log_entry["timestamp"]:
                            if log_entry["timestamp"] < cutoff_time:
                                continue
                        
                        self.logs.append(log_entry)
                        
                        # Update stats
                        self.stats["by_level"][log_entry["level"]] += 1
                        
                        if log_entry["level"] == "error":
                            self.stats["errors"] += 1
                            # Extract error pattern
                            error_snippet = log_entry["raw"][:100]
                            self.stats["error_patterns"][error_snippet] += 1
                        elif log_entry["level"] == "warning":
                            self.stats["warnings"] += 1
                        elif log_entry["level"] == "info":
                            self.stats["info"] += 1
                        
                        if log_entry["timestamp"]:
                            hour = log_entry["timestamp"].strftime("%Y-%m-%d %H:00")
                            self.stats["by_hour"][hour] += 1
                        
                        if log_entry["endpoint"]:
                            self.stats["by_endpoint"][log_entry["endpoint"]] += 1
                        
                        if log_entry["http_status"]:
                            self.stats["http_status_codes"][log_entry["http_status"]] += 1
            
            except Exception as e:
                print(f"  ⚠️  Error reading {log_file}: {e}")
    
    def generate_report(self) -> str:
        """Generate analysis report."""
        report = []
        report.append("=" * 80)
        report.append("LOG ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Log Lines: {self.stats['total_lines']:,}")
        report.append(f"Parsed Entries: {len(self.logs):,}")
        report.append("")
        
        # Log levels
        report.append("LOG LEVELS:")
        for level, count in self.stats["by_level"].most_common():
            percentage = (count / len(self.logs) * 100) if self.logs else 0
            report.append(f"  {level.upper()}: {count:,} ({percentage:.1f}%)")
        report.append("")
        
        # Errors
        if self.stats["errors"] > 0:
            report.append(f"⚠️  ERRORS DETECTED: {self.stats['errors']}")
            report.append("")
            report.append("TOP ERROR PATTERNS:")
            for error, count in list(self.stats["error_patterns"].most_common(10)):
                report.append(f"  ({count}x) {error}")
            report.append("")
        
        # HTTP Status Codes
        if self.stats["http_status_codes"]:
            report.append("HTTP STATUS CODES:")
            for status, count in sorted(self.stats["http_status_codes"].items()):
                report.append(f"  {status}: {count:,}")
            report.append("")
        
        # Top Endpoints
        if self.stats["by_endpoint"]:
            report.append("TOP ENDPOINTS:")
            for endpoint, count in list(self.stats["by_endpoint"].most_common(10)):
                report.append(f"  {endpoint}: {count:,}")
            report.append("")
        
        # Activity by hour
        if self.stats["by_hour"]:
            report.append("ACTIVITY BY HOUR:")
            for hour in sorted(self.stats["by_hour"].keys())[-24:]:  # Last 24 hours
                count = self.stats["by_hour"][hour]
                bar = "█" * min(50, count // 10)
                report.append(f"  {hour}: {bar} ({count:,})")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def export_json(self, output_file: str = "log_analysis.json"):
        """Export analysis to JSON."""
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_lines": self.stats["total_lines"],
            "parsed_entries": len(self.logs),
            "stats": {
                "by_level": dict(self.stats["by_level"]),
                "by_endpoint": dict(self.stats["by_endpoint"].most_common(20)),
                "http_status_codes": dict(self.stats["http_status_codes"]),
                "errors": self.stats["errors"],
                "warnings": self.stats["warnings"],
                "top_error_patterns": [
                    {"pattern": p, "count": c}
                    for p, c in self.stats["error_patterns"].most_common(20)
                ]
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ JSON report saved to: {output_file}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate and analyze application logs")
    parser.add_argument("--dirs", nargs="+", help="Log directories to search")
    parser.add_argument("--hours", type=int, help="Only analyze logs from last N hours")
    parser.add_argument("--json", help="Export to JSON file")
    
    args = parser.parse_args()
    
    aggregator = LogAggregator(log_dirs=args.dirs)
    aggregator.aggregate_logs(hours=args.hours)
    
    report = aggregator.generate_report()
    print(report)
    
    if args.json:
        aggregator.export_json(args.json)

if __name__ == "__main__":
    main()
