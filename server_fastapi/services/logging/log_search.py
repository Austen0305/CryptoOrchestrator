"""
Log Search and Filtering Service
Provides capabilities to search, filter, and analyze application logs.
"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Log directory
LOG_DIR = Path("logs")


class LogSearchService:
    """
    Service for searching and filtering application logs
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize log search service

        Args:
            log_dir: Directory containing log files (default: logs/)
        """
        self.log_dir = log_dir or LOG_DIR
        self.log_files = {
            "app": self.log_dir / "app.log",
            "errors": self.log_dir / "errors.log",
            "audit": self.log_dir / "audit.log",
        }

    def search_logs(
        self,
        query: Optional[str] = None,
        level: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        log_file: str = "app",
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search logs with various filters

        Args:
            query: Text search query (searches in message field)
            level: Log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            user_id: Filter by user ID
            request_id: Filter by request ID
            trace_id: Filter by trace ID
            start_time: Start time for time range filter
            end_time: End time for time range filter
            log_file: Log file to search ("app", "errors", "audit")
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Dictionary with matching log entries and metadata
        """
        log_file_path = self.log_files.get(log_file)
        if not log_file_path or not log_file_path.exists():
            return {"entries": [], "total": 0, "limit": limit, "offset": offset}

        matching_entries = []
        total_matched = 0

        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    # Try to parse as JSON (structured logging)
                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        # Fallback: parse text format
                        entry = self._parse_text_log(line)

                    # Apply filters
                    if not self._matches_filters(
                        entry,
                        query=query,
                        level=level,
                        user_id=user_id,
                        request_id=request_id,
                        trace_id=trace_id,
                        start_time=start_time,
                        end_time=end_time,
                    ):
                        continue

                    total_matched += 1

                    # Apply pagination
                    if total_matched <= offset:
                        continue
                    if len(matching_entries) >= limit:
                        continue

                    matching_entries.append(entry)

        except Exception as e:
            logger.error(f"Error searching logs: {e}", exc_info=True)
            return {
                "entries": [],
                "total": 0,
                "error": str(e),
                "limit": limit,
                "offset": offset,
            }

        return {
            "entries": matching_entries,
            "total": total_matched,
            "limit": limit,
            "offset": offset,
            "has_more": total_matched > offset + len(matching_entries),
        }

    def _parse_text_log(self, line: str) -> Dict[str, Any]:
        """Parse text-format log line into structured format"""
        # Format: "timestamp - logger - level - message"
        parts = line.split(" - ", 3)
        if len(parts) >= 4:
            return {
                "timestamp": parts[0],
                "logger": parts[1],
                "level": parts[2],
                "message": parts[3].strip(),
            }
        return {"message": line.strip(), "timestamp": datetime.utcnow().isoformat()}

    def _matches_filters(
        self,
        entry: Dict[str, Any],
        query: Optional[str] = None,
        level: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> bool:
        """Check if log entry matches all filters"""

        # Text search query
        if query:
            message = entry.get("message", "").lower()
            if query.lower() not in message:
                return False

        # Level filter
        if level:
            entry_level = entry.get("level", "").upper()
            if entry_level != level.upper():
                return False

        # User ID filter
        if user_id:
            entry_user_id = str(entry.get("user_id", ""))
            if entry_user_id != str(user_id):
                return False

        # Request ID filter
        if request_id:
            entry_request_id = entry.get("request_id", "")
            if entry_request_id != request_id:
                return False

        # Trace ID filter
        if trace_id:
            entry_trace_id = entry.get("trace_id", "")
            if entry_trace_id != trace_id:
                return False

        # Time range filter
        if start_time or end_time:
            entry_timestamp = entry.get("timestamp", "")
            try:
                if isinstance(entry_timestamp, str):
                    entry_time = datetime.fromisoformat(
                        entry_timestamp.replace("Z", "+00:00")
                    )
                else:
                    entry_time = entry_timestamp

                if start_time and entry_time < start_time:
                    return False
                if end_time and entry_time > end_time:
                    return False
            except (ValueError, TypeError):
                # If timestamp parsing fails, include the entry
                pass

        return True

    def get_log_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        log_file: str = "app",
    ) -> Dict[str, Any]:
        """
        Get statistics about logs in a time range

        Returns:
            Dictionary with log statistics (counts by level, error rate, etc.)
        """
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()

        log_file_path = self.log_files.get(log_file)
        if not log_file_path or not log_file_path.exists():
            return {
                "total": 0,
                "by_level": {},
                "error_rate": 0.0,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
            }

        level_counts = {}
        total_count = 0
        error_count = 0

        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        entry = self._parse_text_log(line)

                    # Check time range
                    entry_timestamp = entry.get("timestamp", "")
                    try:
                        if isinstance(entry_timestamp, str):
                            entry_time = datetime.fromisoformat(
                                entry_timestamp.replace("Z", "+00:00")
                            )
                        else:
                            entry_time = entry_timestamp

                        if entry_time < start_time or entry_time > end_time:
                            continue
                    except (ValueError, TypeError):
                        continue

                    total_count += 1
                    level = entry.get("level", "UNKNOWN").upper()
                    level_counts[level] = level_counts.get(level, 0) + 1

                    if level in {"ERROR", "CRITICAL"}:
                        error_count += 1

        except Exception as e:
            logger.error(f"Error calculating log statistics: {e}", exc_info=True)
            return {"total": 0, "by_level": {}, "error_rate": 0.0, "error": str(e)}

        error_rate = (error_count / total_count * 100) if total_count > 0 else 0.0

        return {
            "total": total_count,
            "by_level": level_counts,
            "error_count": error_count,
            "error_rate": round(error_rate, 2),
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        }

    def tail_logs(self, log_file: str = "app", lines: int = 50) -> List[Dict[str, Any]]:
        """
        Get the last N lines from a log file (like `tail -n`)

        Args:
            log_file: Log file name ("app", "errors", "audit")
            lines: Number of lines to return

        Returns:
            List of log entries
        """
        log_file_path = self.log_files.get(log_file)
        if not log_file_path or not log_file_path.exists():
            return []

        entries = []

        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                # Read all lines (for small files) or use efficient tail for large files
                all_lines = f.readlines()
                tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

                for line in tail_lines:
                    if not line.strip():
                        continue

                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        entry = self._parse_text_log(line)

                    entries.append(entry)

        except Exception as e:
            logger.error(f"Error tailing logs: {e}", exc_info=True)
            return []

        return entries


def get_log_search_service() -> LogSearchService:
    """Get singleton log search service instance"""
    if not hasattr(get_log_search_service, "_instance"):
        get_log_search_service._instance = LogSearchService()
    return get_log_search_service._instance
