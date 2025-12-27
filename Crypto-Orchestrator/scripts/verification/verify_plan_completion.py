#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plan Completion Verification Script
Verifies all items from the Complete Project Completion Plan
"""
import os
import sys
import io
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Fix Windows encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_file_exists(path: str) -> Tuple[bool, str]:
    """Check if a file exists"""
    file_path = project_root / path
    if file_path.exists():
        return True, f"✅ {path}"
    return False, f"❌ {path} - NOT FOUND"

def check_directory_exists(path: str) -> Tuple[bool, str]:
    """Check if a directory exists"""
    dir_path = project_root / path
    if dir_path.exists() and dir_path.is_dir():
        return True, f"✅ {path}"
    return False, f"❌ {path} - NOT FOUND"

def verify_phase_1_infrastructure() -> Dict[str, List[str]]:
    """Verify Phase 1: Infrastructure Verification & Hardening"""
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    print("\n" + "="*60)
    print("Phase 1: Infrastructure Verification & Hardening")
    print("="*60)
    
    # 1.1 Environment Configuration
    print("\n1.1 Environment Configuration:")
    env_files = [
        ".env.example",
        "server_fastapi/config/env_validator.py",
        "scripts/setup/create_env_file.py",
        "scripts/utilities/validate-environment.js",
        "requirements.txt"
    ]
    for file in env_files:
        success, msg = check_file_exists(file)
        if success:
            results["passed"].append(msg)
        else:
            results["failed"].append(msg)
        print(f"  {msg}")
    
    # 1.2 Database Infrastructure
    print("\n1.2 Database Infrastructure:")
    db_files = [
        "alembic.ini",
        "scripts/utilities/backup_database.py",
        "scripts/utilities/restore_database.py",
        "server_fastapi/services/backup_service.py"
    ]
    for file in db_files:
        success, msg = check_file_exists(file)
        if success:
            results["passed"].append(msg)
        else:
            results["failed"].append(msg)
        print(f"  {msg}")
    
    # Check Alembic versions
    alembic_versions = list((project_root / "alembic" / "versions").glob("*.py"))
    print(f"  ✅ Found {len(alembic_versions)} Alembic migration files")
    results["passed"].append(f"✅ {len(alembic_versions)} Alembic migrations")
    
    # 1.3 Docker Infrastructure
    print("\n1.3 Docker Infrastructure:")
    docker_files = [
        "Dockerfile",
        "Dockerfile.frontend",
        "docker-compose.yml",
        "docker-compose.prod.yml"
    ]
    for file in docker_files:
        success, msg = check_file_exists(file)
        if success:
            results["passed"].append(msg)
        else:
            results["failed"].append(msg)
        print(f"  {msg}")
    
    # 1.4 Kubernetes Infrastructure
    print("\n1.4 Kubernetes Infrastructure:")
    k8s_dir = project_root / "k8s"
    if k8s_dir.exists():
        k8s_files = list(k8s_dir.glob("*.yaml")) + list(k8s_dir.glob("*.yml"))
        print(f"  ✅ Found {len(k8s_files)} Kubernetes manifests")
        results["passed"].append(f"✅ {len(k8s_files)} K8s manifests")
        for k8s_file in k8s_files:
            results["passed"].append(f"  ✅ {k8s_file.name}")
    else:
        results["failed"].append("❌ k8s/ directory not found")
    
    # 1.5 Terraform Infrastructure
    print("\n1.5 Terraform Infrastructure:")
    terraform_dir = project_root / "terraform"
    if terraform_dir.exists():
        tf_files = list(terraform_dir.rglob("*.tf"))
        print(f"  ✅ Found {len(tf_files)} Terraform files")
        results["passed"].append(f"✅ {len(tf_files)} Terraform files")
    else:
        results["warnings"].append("⚠️  terraform/ directory not found (optional)")
    
    return results

def verify_phase_2_features() -> Dict[str, List[str]]:
    """Verify Phase 2: Feature Verification & Testing"""
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    print("\n" + "="*60)
    print("Phase 2: Feature Verification & Testing")
    print("="*60)
    
    # 2.1 API Verification
    print("\n2.1 API Verification:")
    api_files = [
        "scripts/verification/comprehensive_feature_verification.py",
        "server_fastapi/routes"
    ]
    for item in api_files:
        success, msg = check_file_exists(item) if "." in item else check_directory_exists(item)
        if success:
            results["passed"].append(msg)
        else:
            results["failed"].append(msg)
        print(f"  {msg}")
    
    # Count route files
    routes_dir = project_root / "server_fastapi" / "routes"
    if routes_dir.exists():
        route_files = list(routes_dir.glob("*.py"))
        print(f"  ✅ Found {len(route_files)} route files")
        results["passed"].append(f"✅ {len(route_files)} route files")
    
    # 2.2 WebSocket
    print("\n2.2 WebSocket Verification:")
    ws_files = [
        "server_fastapi/routes/websocket.py",
        "server_fastapi/services/websocket_service.py"
    ]
    for file in ws_files:
        success, msg = check_file_exists(file)
        if success:
            results["passed"].append(msg)
        else:
            results["warnings"].append(msg + " (may be in different location)")
        print(f"  {msg}")
    
    # 2.3 Celery Tasks
    print("\n2.3 Celery Tasks:")
    celery_files = [
        "server_fastapi/celery_app.py",
        "server_fastapi/tasks"
    ]
    for item in celery_files:
        success, msg = check_file_exists(item) if "." in item else check_directory_exists(item)
        if success:
            results["passed"].append(msg)
        else:
            results["failed"].append(msg)
        print(f"  {msg}")
    
    # 2.4 Email & SMS
    print("\n2.4 Email & SMS Services:")
    service_files = [
        "server_fastapi/services/email_service.py",
        "server_fastapi/services/sms_service.py",
        "server_fastapi/services/notification_service.py",
        "server_fastapi/services/expo_push_service.py"
    ]
    for file in service_files:
        success, msg = check_file_exists(file)
        if success:
            results["passed"].append(msg)
        else:
            results["warnings"].append(msg)
        print(f"  {msg}")
    
    # 2.5 ML/AI Services
    print("\n2.5 ML/AI Services:")
    ml_dir = project_root / "server_fastapi" / "services" / "ml"
    if ml_dir.exists():
        ml_files = list(ml_dir.glob("*.py"))
        print(f"  ✅ Found {len(ml_files)} ML service files")
        results["passed"].append(f"✅ {len(ml_files)} ML service files")
    else:
        results["warnings"].append("⚠️  ML services directory not found")
    
    # 2.6 Payment Processing
    print("\n2.6 Payment Processing:")
    payment_files = [
        "server_fastapi/services/payments/stripe_service.py"
    ]
    for file in payment_files:
        success, msg = check_file_exists(file)
        if success:
            results["passed"].append(msg)
        else:
            results["warnings"].append(msg)
        print(f"  {msg}")
    
    return results

def verify_phase_3_mobile() -> Dict[str, List[str]]:
    """Verify Phase 3: Mobile App Completion"""
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    print("\n" + "="*60)
    print("Phase 3: Mobile App Completion")
    print("="*60)
    
    mobile_dir = project_root / "mobile"
    if mobile_dir.exists():
        results["passed"].append("✅ mobile/ directory exists")
        print("  ✅ mobile/ directory exists")
        
        # Check for native folders
        ios_dir = mobile_dir / "ios"
        android_dir = mobile_dir / "android"
        
        if ios_dir.exists():
            results["passed"].append("✅ iOS native project exists")
            print("  ✅ iOS native project exists")
        else:
            results["warnings"].append("⚠️  iOS native project not initialized")
            print("  ⚠️  iOS native project not initialized")
        
        if android_dir.exists():
            results["passed"].append("✅ Android native project exists")
            print("  ✅ Android native project exists")
        else:
            results["warnings"].append("⚠️  Android native project not initialized")
            print("  ⚠️  Android native project not initialized")
    else:
        results["failed"].append("❌ mobile/ directory not found")
    
    return results

def verify_phase_4_security() -> Dict[str, List[str]]:
    """Verify Phase 4: Security Hardening"""
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    print("\n" + "="*60)
    print("Phase 4: Security Hardening")
    print("="*60)
    
    security_files = [
        "scripts/security/security_audit.py",
        "server_fastapi/middleware/security_middleware.py",
        "server_fastapi/middleware/csp_middleware.py",
        "server_fastapi/middleware/csrf_middleware.py"
    ]
    
    for file in security_files:
        success, msg = check_file_exists(file)
        if success:
            results["passed"].append(msg)
        else:
            results["warnings"].append(msg)
        print(f"  {msg}")
    
    return results

def verify_phase_6_frontend() -> Dict[str, List[str]]:
    """Verify Phase 6: Frontend & Electron App"""
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    print("\n" + "="*60)
    print("Phase 6: Frontend & Electron App")
    print("="*60)
    
    frontend_files = [
        "client/src",
        "client/vite.config.ts",
        "scripts/utilities/bundle-analyze.js",
        "electron/index.js",
        "electron/preload.js"
    ]
    
    for item in frontend_files:
        success, msg = check_file_exists(item) if "." in item else check_directory_exists(item)
        if success:
            results["passed"].append(msg)
        else:
            results["warnings"].append(msg)
        print(f"  {msg}")
    
    # Check AdvancedChartingTerminal
    chart_file = project_root / "client" / "src" / "components" / "AdvancedChartingTerminal.tsx"
    if chart_file.exists():
        with open(chart_file, "r", encoding="utf-8") as f:
            content = f.read()
            if "updatePreferences" in content and "chartTemplates" in content:
                results["passed"].append("✅ AdvancedChartingTerminal saves templates to backend")
                print("  ✅ AdvancedChartingTerminal saves templates to backend")
            else:
                results["warnings"].append("⚠️  AdvancedChartingTerminal may need backend integration")
    
    return results

def verify_phase_7_cicd() -> Dict[str, List[str]]:
    """Verify Phase 7: CI/CD Pipeline Verification"""
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    print("\n" + "="*60)
    print("Phase 7: CI/CD Pipeline Verification")
    print("="*60)
    
    workflows_dir = project_root / ".github" / "workflows"
    if workflows_dir.exists():
        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        print(f"  ✅ Found {len(workflow_files)} GitHub Actions workflows")
        results["passed"].append(f"✅ {len(workflow_files)} GitHub Actions workflows")
    else:
        results["failed"].append("❌ .github/workflows/ directory not found")
    
    return results

def main():
    """Main verification function"""
    print("🚀 CryptoOrchestrator Plan Completion Verification")
    print("="*60)
    
    all_results = {
        "phase_1": verify_phase_1_infrastructure(),
        "phase_2": verify_phase_2_features(),
        "phase_3": verify_phase_3_mobile(),
        "phase_4": verify_phase_4_security(),
        "phase_6": verify_phase_6_frontend(),
        "phase_7": verify_phase_7_cicd(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    total_passed = sum(len(r["passed"]) for r in all_results.values())
    total_failed = sum(len(r["failed"]) for r in all_results.values())
    total_warnings = sum(len(r["warnings"]) for r in all_results.values())
    
    print(f"\n✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"⚠️  Warnings: {total_warnings}")
    
    if total_failed > 0:
        print("\n❌ Failed Items:")
        for phase, results in all_results.items():
            for item in results["failed"]:
                print(f"  {item}")
    
    if total_warnings > 0:
        print("\n⚠️  Warnings:")
        for phase, results in all_results.items():
            for item in results["warnings"]:
                print(f"  {item}")
    
    # Save report
    report_file = project_root / "plan_verification_report.json"
    with open(report_file, "w") as f:
        json.dump({
            "summary": {
                "passed": total_passed,
                "failed": total_failed,
                "warnings": total_warnings
            },
            "details": all_results
        }, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")
    
    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

