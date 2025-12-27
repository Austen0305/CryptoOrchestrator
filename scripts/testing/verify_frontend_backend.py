#!/usr/bin/env python3
"""
Frontend-Backend Integration Verification Script

This script verifies that frontend API calls match backend routes by:
1. Parsing frontend API functions from client/src/lib/api.ts
2. Checking backend routes from server_fastapi/routes/*.py
3. Comparing endpoints, methods, and parameters
4. Reporting mismatches

Usage:
    python scripts/testing/verify_frontend_backend.py
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

# Add server_fastapi to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server_fastapi"))

@dataclass
class FrontendEndpoint:
    """Represents a frontend API endpoint call"""
    method: str
    path: str
    function_name: str
    file: str
    line: int

@dataclass
class BackendRoute:
    """Represents a backend API route"""
    method: str
    path: str
    handler_name: str
    file: str

def parse_frontend_api_file(file_path: Path) -> List[FrontendEndpoint]:
    """Parse frontend API functions from api.ts file"""
    endpoints = []
    
    if not file_path.exists():
        print(f"Warning: Frontend API file not found: {file_path}")
        return endpoints
    
    content = file_path.read_text(encoding='utf-8')
    
    # Pattern to match apiRequest calls
    # Matches: apiRequest<Type>(`/api/path`, { method: "METHOD" })
    api_request_pattern = re.compile(
        r'apiRequest[^`]*`(/api/[^`]+)`[^}]*method:\s*["\'](\w+)["\']',
        re.MULTILINE
    )
    
    lines = content.split('\n')
    for match in api_request_pattern.finditer(content):
        path = match.group(1)
        method = match.group(2).upper()
        
        # Find line number
        line_num = content[:match.start()].count('\n') + 1
        
        # Find function name (look backwards for function definition)
        before_match = content[:match.start()]
        func_match = re.search(r'(\w+)\s*[:=]\s*\([^)]*\)\s*=>', before_match)
        func_name = func_match.group(1) if func_match else "unknown"
        
        endpoints.append(FrontendEndpoint(
            method=method,
            path=path,
            function_name=func_name,
            file=str(file_path.relative_to(Path(__file__).parent.parent.parent)),
            line=line_num
        ))
    
    return endpoints

def parse_backend_routes() -> List[BackendRoute]:
    """Parse backend routes from route files"""
    routes = []
    routes_dir = Path(__file__).parent.parent.parent / "server_fastapi" / "routes"
    
    if not routes_dir.exists():
        print(f"Warning: Backend routes directory not found: {routes_dir}")
        return routes
    
    # Route decorator patterns
    route_patterns = [
        (r'@router\.(get|post|put|patch|delete)\s*\(["\']([^"\']+)["\']', 'router'),
        (r'@app\.(get|post|put|patch|delete)\s*\(["\']([^"\']+)["\']', 'app'),
    ]
    
    for route_file in routes_dir.glob("*.py"):
        if route_file.name.startswith("__"):
            continue
            
        content = route_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, router_type in route_patterns:
                match = re.search(pattern, line)
                if match:
                    method = match.group(1).upper()
                    path = match.group(2)
                    
                    # Find handler function name (next def statement)
                    handler_match = None
                    for next_line in lines[line_num:line_num+10]:
                        def_match = re.search(r'^async def (\w+)', next_line)
                        if def_match:
                            handler_match = def_match.group(1)
                            break
                    
                    handler_name = handler_match or "unknown"
                    
                    routes.append(BackendRoute(
                        method=method,
                        path=path,
                        handler_name=handler_name,
                        file=str(route_file.relative_to(Path(__file__).parent.parent.parent))
                    ))
    
    return routes

def normalize_path(path: str) -> str:
    """Normalize path for comparison (remove query params, normalize slashes)"""
    # Remove query parameters
    path = path.split('?')[0]
    # Normalize trailing slashes
    path = path.rstrip('/')
    if not path:
        path = '/'
    return path

def find_matching_backend_route(frontend_endpoint: FrontendEndpoint, backend_routes: List[BackendRoute]) -> Optional[BackendRoute]:
    """Find matching backend route for frontend endpoint"""
    normalized_frontend_path = normalize_path(frontend_endpoint.path)
    
    for backend_route in backend_routes:
        # Normalize backend path (may have path params like {id})
        backend_path = normalize_path(backend_route.path)
        
        # Replace path params with regex pattern
        backend_path_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', backend_path)
        backend_path_pattern = backend_path_pattern.replace('/', r'\/')
        
        if (backend_route.method == frontend_endpoint.method and 
            re.match(f'^{backend_path_pattern}$', normalized_frontend_path)):
            return backend_route
    
    return None

def verify_integration():
    """Main verification function"""
    print("=" * 80)
    print("Frontend-Backend Integration Verification")
    print("=" * 80)
    print()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Parse frontend endpoints
    print("Parsing frontend API calls...")
    frontend_api_file = project_root / "client" / "src" / "lib" / "api.ts"
    frontend_endpoints = parse_frontend_api_file(frontend_api_file)
    print(f"Found {len(frontend_endpoints)} frontend API calls")
    print()
    
    # Parse backend routes
    print("Parsing backend routes...")
    backend_routes = parse_backend_routes()
    print(f"Found {len(backend_routes)} backend routes")
    print()
    
    # Verify each frontend endpoint
    print("Verifying frontend-backend integration...")
    print()
    
    matched = []
    unmatched = []
    
    for endpoint in frontend_endpoints:
        matching_route = find_matching_backend_route(endpoint, backend_routes)
        if matching_route:
            matched.append((endpoint, matching_route))
        else:
            unmatched.append(endpoint)
    
    # Report results
    print(f"✅ Matched: {len(matched)}/{len(frontend_endpoints)} endpoints")
    print(f"❌ Unmatched: {len(unmatched)}/{len(frontend_endpoints)} endpoints")
    print()
    
    if unmatched:
        print("=" * 80)
        print("UNMATCHED FRONTEND ENDPOINTS")
        print("=" * 80)
        for endpoint in unmatched:
            print(f"❌ {endpoint.method} {endpoint.path}")
            print(f"   Function: {endpoint.function_name}")
            print(f"   Location: {endpoint.file}:{endpoint.line}")
            print()
    
    # Summary of matched endpoints
    if matched:
        print("=" * 80)
        print("MATCHED ENDPOINTS (Sample)")
        print("=" * 80)
        for endpoint, route in matched[:10]:  # Show first 10
            print(f"✅ {endpoint.method} {endpoint.path}")
            print(f"   Frontend: {endpoint.function_name} ({endpoint.file}:{endpoint.line})")
            print(f"   Backend:  {route.handler_name} ({route.file})")
            print()
        if len(matched) > 10:
            print(f"... and {len(matched) - 10} more matched endpoints")
            print()
    
    # Generate report
    report = {
        "total_frontend_endpoints": len(frontend_endpoints),
        "total_backend_routes": len(backend_routes),
        "matched": len(matched),
        "unmatched": len(unmatched),
        "match_rate": f"{(len(matched) / len(frontend_endpoints) * 100):.1f}%" if frontend_endpoints else "0%",
        "unmatched_endpoints": [
            {
                "method": e.method,
                "path": e.path,
                "function": e.function_name,
                "file": e.file,
                "line": e.line
            }
            for e in unmatched
        ]
    }
    
    report_file = project_root / "test-results" / "frontend_backend_verification.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2))
    print(f"Report saved to: {report_file}")
    print()
    
    return len(unmatched) == 0

if __name__ == "__main__":
    success = verify_integration()
    sys.exit(0 if success else 1)









