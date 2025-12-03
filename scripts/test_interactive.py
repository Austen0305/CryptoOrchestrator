#!/usr/bin/env python3
"""
Interactive Testing CLI for CryptoOrchestrator
Wizard-style interface to guide through manual testing phases
"""
import subprocess
import sys
import os
from datetime import datetime


class Colors:
    """Terminal color codes"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * len(text))


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def confirm(prompt):
    """Ask for confirmation"""
    response = get_input(f"{prompt} (y/n)", "y").lower()
    return response in ['y', 'yes']


def run_command(command, description):
    """Run a shell command"""
    print_info(f"Running: {description}")
    print(f"Command: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=False, text=True)
        if result.returncode == 0:
            print_success(f"{description} completed")
            return True
        else:
            print_error(f"{description} failed with code {result.returncode}")
            return False
    except Exception as e:
        print_error(f"Error running command: {str(e)}")
        return False


def main_menu():
    """Display main menu"""
    print_header("🧪 CryptoOrchestrator - Interactive Testing CLI")
    print("\nSelect testing phase:")
    print("1. Phase 1: Infrastructure Validation")
    print("2. Phase 2: Security Testing")
    print("3. Phase 3: Wallet & Payments (Manual)")
    print("4. Phase 4: Trading & Bots")
    print("5. Phase 9: E2E Tests")
    print("6. Phase 10: Load & Performance")
    print("7. Chaos Engineering Tests")
    print("8. Run All Automated Tests")
    print("9. View Test Documentation")
    print("0. Exit")
    
    choice = get_input("\nEnter your choice", "1")
    return choice


def phase1_infrastructure():
    """Phase 1: Infrastructure tests"""
    print_header("Phase 1: Infrastructure Validation")
    
    print("\n📋 This phase will test:")
    print("  - Backend health endpoints")
    print("  - Database connectivity")
    print("  - Redis connectivity")
    print("  - API endpoints")
    print("  - CORS configuration")
    
    if not confirm("\nProceed with infrastructure tests?"):
        return
    
    # Check if server is running
    print_info("Checking if server is running...")
    if confirm("Is the FastAPI server running? (If not, start it with: npm run dev:fastapi)"):
        run_command("python scripts/test_infrastructure.py", "Infrastructure Tests")
    else:
        print_warning("Please start the server first: npm run dev:fastapi")


def phase2_security():
    """Phase 2: Security tests"""
    print_header("Phase 2: Security Testing")
    
    print("\n🔒 This phase will test:")
    print("  - SQL injection protection")
    print("  - XSS protection")
    print("  - Rate limiting")
    print("  - Security headers")
    print("  - Password validation")
    print("  - CORS restrictions")
    
    if not confirm("\nProceed with security tests?"):
        return
    
    if confirm("Is the FastAPI server running?"):
        run_command("python scripts/test_security.py", "Security Tests")
    else:
        print_warning("Please start the server first: npm run dev:fastapi")


def phase3_payments():
    """Phase 3: Payments (manual)"""
    print_header("Phase 3: Wallet & Payments (Manual Testing)")
    
    print("\n💳 Manual testing required for:")
    print("  - Stripe test card payments")
    print("  - 3D Secure flow")
    print("  - Withdrawal requests")
    print("  - Transaction history")
    
    print_info("\n📖 Detailed instructions in: docs/TESTING_GUIDE.md (Phase 3)")
    
    if confirm("Open testing guide?"):
        if sys.platform == "darwin":
            subprocess.run(["open", "docs/TESTING_GUIDE.md"])
        elif sys.platform == "win32":
            subprocess.run(["start", "docs/TESTING_GUIDE.md"], shell=True)
        else:
            subprocess.run(["xdg-open", "docs/TESTING_GUIDE.md"])


def phase9_e2e():
    """Phase 9: E2E tests"""
    print_header("Phase 9: End-to-End Tests")
    
    print("\n🎭 E2E tests will validate:")
    print("  - Registration → trading flow")
    print("  - Wallet operations")
    print("  - Bot lifecycle")
    print("  - Navigation")
    print("  - Error handling")
    
    if not confirm("\nProceed with E2E tests?"):
        return
    
    print_info("Make sure both frontend and backend are running")
    if confirm("Are frontend and backend running?"):
        if confirm("Run in headless mode?"):
            run_command("npm run test:e2e", "E2E Tests (Headless)")
        else:
            run_command("npm run test:e2e:ui", "E2E Tests (UI Mode)")
    else:
        print_warning("Start frontend: npm run dev")
        print_warning("Start backend: npm run dev:fastapi")


def phase10_performance():
    """Phase 10: Performance tests"""
    print_header("Phase 10: Load & Performance Testing")
    
    print("\n⚡ Performance tests will measure:")
    print("  - API response times (p50/p95/p99)")
    print("  - Throughput (requests/second)")
    print("  - Concurrent request handling")
    print("  - Error rates under load")
    
    if not confirm("\nProceed with performance tests?"):
        return
    
    if confirm("Is the FastAPI server running?"):
        concurrent = get_input("Number of concurrent requests", "50")
        total = get_input("Total requests", "500")
        
        run_command(
            f"python scripts/load_test.py --concurrent {concurrent} --total {total}",
            "Load Tests"
        )
    else:
        print_warning("Please start the server first: npm run dev:fastapi")


def chaos_tests():
    """Chaos engineering tests"""
    print_header("Chaos Engineering Tests")
    
    print("\n🔥 Chaos tests will simulate:")
    print("  - Connection timeouts")
    print("  - Malformed requests")
    print("  - Rapid request floods")
    print("  - Large payloads")
    print("  - Concurrent operations")
    print("  - Invalid endpoints")
    
    print_warning("\n⚠️  WARNING: These tests intentionally cause failures")
    
    if not confirm("\nProceed with chaos tests?"):
        return
    
    if confirm("Is the FastAPI server running?"):
        run_command("python scripts/test_chaos.py", "Chaos Engineering Tests")
    else:
        print_warning("Please start the server first: npm run dev:fastapi")


def run_all_tests():
    """Run all automated tests"""
    print_header("Run All Automated Tests")
    
    print("\n🚀 This will run:")
    print("  1. Infrastructure tests")
    print("  2. Security tests")
    print("  3. Load tests")
    print("  4. Chaos tests")
    print("  5. Comprehensive pre-deployment validation")
    
    if not confirm("\nProceed with all tests?"):
        return
    
    if not confirm("Is the FastAPI server running?"):
        print_warning("Please start the server first: npm run dev:fastapi")
        return
    
    run_command("python scripts/test_pre_deploy.py", "Comprehensive Test Suite")


def view_documentation():
    """View test documentation"""
    print_header("Test Documentation")
    
    print("\n📖 Available documentation:")
    print("  1. Testing Guide (Complete checklist)")
    print("  2. Testing Quick Reference")
    print("  3. Deployment Scorecard")
    print("  4. Pre-Deployment Status")
    
    choice = get_input("\nWhich document? (1-4)", "1")
    
    docs = {
        "1": "docs/TESTING_GUIDE.md",
        "2": "docs/TESTING_README.md",
        "3": "docs/DEPLOYMENT_SCORECARD.md",
        "4": "docs/PRE_DEPLOYMENT_STATUS.md",
    }
    
    doc_path = docs.get(choice)
    if doc_path and os.path.exists(doc_path):
        print_info(f"Opening: {doc_path}")
        if sys.platform == "darwin":
            subprocess.run(["open", doc_path])
        elif sys.platform == "win32":
            subprocess.run(["start", doc_path], shell=True)
        else:
            subprocess.run(["xdg-open", doc_path])
    else:
        print_error("Document not found")


def main():
    """Main CLI loop"""
    while True:
        choice = main_menu()
        
        if choice == "1":
            phase1_infrastructure()
        elif choice == "2":
            phase2_security()
        elif choice == "3":
            phase3_payments()
        elif choice == "4":
            print_info("Phase 4 tests: npm run test (backend) or manual testing")
        elif choice == "5":
            phase9_e2e()
        elif choice == "6":
            phase10_performance()
        elif choice == "7":
            chaos_tests()
        elif choice == "8":
            run_all_tests()
        elif choice == "9":
            view_documentation()
        elif choice == "0":
            print_success("Goodbye! 👋")
            break
        else:
            print_error("Invalid choice. Please try again.")
        
        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n")
        print_warning("Testing interrupted by user")
        sys.exit(0)
