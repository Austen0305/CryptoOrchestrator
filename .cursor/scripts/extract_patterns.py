#!/usr/bin/env python3
"""
Pattern Extraction Script
Extracts patterns from codebase and stores in knowledge graph

Usage:
    python .cursor/scripts/extract_patterns.py
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def extract_route_patterns() -> List[Dict[str, Any]]:
    """Extract FastAPI route patterns"""
    patterns = []
    route_dir = Path("server_fastapi/routes")
    
    if not route_dir.exists():
        return patterns
    
    for file in route_dir.glob("*.py"):
        try:
            content = file.read_text(encoding="utf-8")
            
            # Extract route decorators
            routes = re.findall(r'@router\.(get|post|put|patch|delete)', content)
            
            # Extract dependencies
            deps = re.findall(r'Depends\(([^)]+)\)', content)
            
            # Check for caching
            cached = "@cached" in content
            
            # Check for pagination
            pagination = "page:" in content and "page_size:" in content
            
            # Check for authentication
            auth = "get_current_user" in content or "validate_jwt" in content
            
            # Check for user_id extraction
            user_id_helper = "_get_user_id" in content
            
            if routes:
                # Use simple path normalization
                file_str = str(file).replace("\\", "/")
                cwd_str = str(Path.cwd()).replace("\\", "/")
                if file_str.startswith(cwd_str):
                    file_str = file_str[len(cwd_str) + 1:]
                patterns.append({
                    "file": file_str,
                    "type": "route",
                    "routes": len(routes),
                    "dependencies": len(set(deps)),
                    "cached": cached,
                    "pagination": pagination,
                    "auth": auth,
                    "user_id_helper": user_id_helper,
                    "pattern": "FastAPI Route Pattern"
                })
        except Exception as e:
            print(f"Error processing {str(file)}: {e}")
    
    return patterns

def extract_service_patterns() -> List[Dict[str, Any]]:
    """Extract service patterns"""
    patterns = []
    service_dir = Path("server_fastapi/services")
    
    if not service_dir.exists():
        return patterns
    
    for file in service_dir.rglob("*.py"):
        try:
            content = file.read_text(encoding="utf-8")
            
            # Find service classes
            services = re.findall(r'class (\w+Service)', content)
            
            # Check for repository usage
            has_repository = "Repository" in content or "self.repository" in content
            
            # Check if stateless
            stateless = "__init__" in content and "self.repository" in content
            
            # Check for async
            async_methods = len(re.findall(r'async def ', content))
            
            if services:
                patterns.append({
                    "file": str(file.relative_to(Path.cwd())),
                    "type": "service",
                    "services": services,
                    "has_repository": has_repository,
                    "stateless": stateless,
                    "async_methods": async_methods,
                    "pattern": "Service Layer Pattern"
                })
        except Exception as e:
            print(f"Error processing {str(file)}: {e}")
    
    return patterns

def extract_repository_patterns() -> List[Dict[str, Any]]:
    """Extract repository patterns"""
    patterns = []
    repo_dir = Path("server_fastapi/repositories")
    
    if not repo_dir.exists():
        return patterns
    
    for file in repo_dir.glob("*.py"):
        try:
            content = file.read_text(encoding="utf-8")
            
            # Find repository classes
            repos = re.findall(r'class (\w+Repository)', content)
            
            # Check for eager loading
            eager_loading = "selectinload" in content or "joinedload" in content
            
            # Check for async
            async_methods = len(re.findall(r'async def ', content))
            
            if repos:
                file_str = str(file).replace("\\", "/")
                cwd_str = str(Path.cwd()).replace("\\", "/")
                if file_str.startswith(cwd_str):
                    file_str = file_str[len(cwd_str) + 1:]
                patterns.append({
                    "file": file_str,
                    "type": "repository",
                    "repositories": repos,
                    "eager_loading": eager_loading,
                    "async_methods": async_methods,
                    "pattern": "Repository Pattern"
                })
        except Exception as e:
            print(f"Error processing {str(file)}: {e}")
    
    return patterns

def extract_hook_patterns() -> List[Dict[str, Any]]:
    """Extract React Query hook patterns"""
    patterns = []
    hook_dir = Path("client/src/hooks")
    
    if not hook_dir.exists():
        return patterns
    
    for file in hook_dir.glob("*.ts"):
        try:
            content = file.read_text(encoding="utf-8")
            
            # Find useQuery hooks
            queries = len(re.findall(r'useQuery\(', content))
            
            # Find useMutation hooks
            mutations = len(re.findall(r'useMutation\(', content))
            
            # Check for optimistic updates
            optimistic = "onMutate" in content
            
            # Check for authentication
            auth = "useAuth" in content
            
            # Check for query invalidation
            invalidation = "invalidateQueries" in content
            
            if queries > 0 or mutations > 0:
                file_str = str(file).replace("\\", "/")
                if file_str.startswith(str(Path.cwd()).replace("\\", "/")):
                    file_str = file_str[len(str(Path.cwd()).replace("\\", "/")) + 1:]
                patterns.append({
                    "file": file_str,
                    "type": "hook",
                    "queries": queries,
                    "mutations": mutations,
                    "optimistic": optimistic,
                    "auth": auth,
                    "invalidation": invalidation,
                    "pattern": "React Query Hook Pattern"
                })
        except Exception as e:
            print(f"Error processing {str(file)}: {e}")
    
    return patterns

def generate_pattern_report(patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate pattern statistics report"""
    report = {
        "extraction_date": datetime.now().isoformat(),
        "current_date": "2025-12-11",
        "total_patterns": len(patterns),
        "by_type": {},
        "by_pattern": {},
        "statistics": {},
        "patterns": patterns
    }
    
    # Count by type
    for pattern in patterns:
        pattern_type = pattern["type"]
        report["by_type"][pattern_type] = report["by_type"].get(pattern_type, 0) + 1
    
    # Count by pattern name
    for pattern in patterns:
        pattern_name = pattern.get("pattern", "Unknown")
        report["by_pattern"][pattern_name] = report["by_pattern"].get(pattern_name, 0) + 1
    
    # Calculate statistics
    if patterns:
        route_patterns = [p for p in patterns if p["type"] == "route"]
        service_patterns = [p for p in patterns if p["type"] == "service"]
        hook_patterns = [p for p in patterns if p["type"] == "hook"]
        
        report["statistics"] = {
            "routes": {
                "total": len(route_patterns),
                "with_caching": sum(1 for p in route_patterns if p.get("cached", False)),
                "with_pagination": sum(1 for p in route_patterns if p.get("pagination", False)),
                "with_auth": sum(1 for p in route_patterns if p.get("auth", False)),
            },
            "services": {
                "total": len(service_patterns),
                "stateless": sum(1 for p in service_patterns if p.get("stateless", False)),
                "with_repository": sum(1 for p in service_patterns if p.get("has_repository", False)),
            },
            "hooks": {
                "total": len(hook_patterns),
                "with_optimistic": sum(1 for p in hook_patterns if p.get("optimistic", False)),
                "with_auth": sum(1 for p in hook_patterns if p.get("auth", False)),
                "with_invalidation": sum(1 for p in hook_patterns if p.get("invalidation", False)),
            }
        }
    
    return report

def main():
    """Main extraction function"""
    import sys
    import io
    
    # Fix Windows console encoding for emojis
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("Extracting patterns from codebase...")
    print(f"Current Date: December 11, 2025\n")
    
    # Extract patterns
    print("Extracting route patterns...")
    route_patterns = extract_route_patterns()
    print(f"   Found {len(route_patterns)} route files")
    
    print("Extracting service patterns...")
    service_patterns = extract_service_patterns()
    print(f"   Found {len(service_patterns)} service files")
    
    print("Extracting repository patterns...")
    repo_patterns = extract_repository_patterns()
    print(f"   Found {len(repo_patterns)} repository files")
    
    print("Extracting hook patterns...")
    hook_patterns = extract_hook_patterns()
    print(f"   Found {len(hook_patterns)} hook files")
    
    all_patterns = route_patterns + service_patterns + repo_patterns + hook_patterns
    
    # Generate report
    report = generate_pattern_report(all_patterns)
    
    # Save report
    output_dir = Path(".cursor/pattern-reports")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"pattern-extraction-{datetime.now().strftime('%Y%m%d')}.json"
    output_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    
    print(f"\nExtracted {len(all_patterns)} patterns")
    print(f"Report saved to {output_file}")
    
    # Print summary
    print("\nPattern Summary:")
    print(f"  Total Files: {len(all_patterns)}")
    print(f"\n  By Type:")
    for pattern_type, count in report["by_type"].items():
        print(f"    - {pattern_type}: {count} files")
    
    print(f"\n  By Pattern:")
    for pattern_name, count in report["by_pattern"].items():
        print(f"    - {pattern_name}: {count} files")
    
    if report.get("statistics"):
        stats = report["statistics"]
        print(f"\n  Statistics:")
        if "routes" in stats:
            r = stats["routes"]
            print(f"    Routes: {r['total']} total, {r.get('with_caching', 0)} cached, {r.get('with_pagination', 0)} paginated")
        if "services" in stats:
            s = stats["services"]
            print(f"    Services: {s['total']} total, {s.get('stateless', 0)} stateless, {s.get('with_repository', 0)} with repository")
        if "hooks" in stats:
            h = stats["hooks"]
            print(f"    Hooks: {h['total']} total, {h.get('with_optimistic', 0)} optimistic, {h.get('with_auth', 0)} with auth")

if __name__ == "__main__":
    main()
