#!/usr/bin/env python3
"""
National Water Infrastructure Monitoring System
Comprehensive System Verification Script
Version 2.0.0
"""

import sys
import os
import json
import subprocess
from typing import Dict, List, Tuple
from pathlib import Path

# Color codes for terminal output
import sys
import io

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class SystemVerifier:
    """Verify all system components and requirements."""
    
    def __init__(self):
        self.results = []
        self.warnings = []
        self.errors = []
    
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
    
    def print_check(self, name: str, status: bool, message: str = ""):
        """Print check result."""
        if status:
            print(f"{GREEN}[OK]{RESET} {name}")
            if message:
                print(f"  {message}")
            self.results.append((name, True, message))
        else:
            print(f"{RED}[FAIL]{RESET} {name}")
            if message:
                print(f"  {RED}{message}{RESET}")
            self.errors.append((name, message))
            self.results.append((name, False, message))
    
    def print_warning(self, name: str, message: str):
        """Print warning."""
        print(f"{YELLOW}[WARN]{RESET} {name}")
        print(f"  {YELLOW}{message}{RESET}")
        self.warnings.append((name, message))
    
    def check_python_version(self):
        """Check Python version."""
        self.print_header("Python Environment")
        
        version = sys.version_info
        required = (3, 12)
        
        if version >= required:
            self.print_check(
                "Python Version",
                True,
                f"Python {version.major}.{version.minor}.{version.micro}"
            )
        else:
            self.print_check(
                "Python Version",
                False,
                f"Python {version.major}.{version.minor} (requires 3.12+)"
            )
    
    def check_docker(self):
        """Check Docker installation."""
        self.print_header("Docker Environment")
        
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.print_check("Docker Installed", True, result.stdout.strip())
            else:
                self.print_check("Docker Installed", False, "Docker not found")
        except Exception as e:
            self.print_check("Docker Installed", False, str(e))
        
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.print_check("Docker Compose", True, result.stdout.strip())
            else:
                self.print_check("Docker Compose", False, "Docker Compose not found")
        except Exception as e:
            self.print_check("Docker Compose", False, str(e))
    
    def check_project_structure(self):
        """Check project directory structure."""
        self.print_header("Project Structure")
        
        required_dirs = [
            "backend",
            "backend/app",
            "backend/app/api",
            "backend/app/core",
            "backend/app/models",
            "backend/app/services",
            "backend/app/mqtt",
            "backend/app/websocket",
            "frontend-control-room",
            "mobile-app",
            "iot-gateway",
            "kubernetes",
            "infrastructure",
            "docs"
        ]
        
        for dir_path in required_dirs:
            exists = Path(dir_path).exists()
            self.print_check(f"Directory: {dir_path}", exists)
    
    def check_required_files(self):
        """Check required configuration files."""
        self.print_header("Configuration Files")
        
        required_files = [
            "backend/requirements.txt",
            "backend/Dockerfile",
            "backend/app/main.py",
            "backend/app/core/config.py",
            "backend/app/core/security.py",
            "backend/app/core/database.py",
            "docker-compose.yml",
            "README.md",
            ".gitignore"
        ]
        
        for file_path in required_files:
            exists = Path(file_path).exists()
            self.print_check(f"File: {file_path}", exists)
    
    def check_environment_config(self):
        """Check environment configuration."""
        self.print_header("Environment Configuration")
        
        env_file = Path("backend/.env")
        if env_file.exists():
            self.print_check("Environment File", True, "backend/.env exists")
            
            # Check critical variables
            with open(env_file, 'r') as f:
                content = f.read()
                
                critical_vars = [
                    "DATABASE_URL_MYSQL",
                    "DATABASE_URL_POSTGRES",
                    "REDIS_URL",
                    "SECRET_KEY",
                    "S3_BUCKET",
                    "S3_ACCESS_KEY"
                ]
                
                for var in critical_vars:
                    if var in content and not f"{var}=${{" in content:
                        self.print_check(f"Variable: {var}", True, "Configured")
                    else:
                        self.print_warning(
                            f"Variable: {var}",
                            "Not configured or using placeholder"
                        )
        else:
            self.print_check("Environment File", False, "backend/.env not found")
    
    def check_database_models(self):
        """Check database models."""
        self.print_header("Database Models")
        
        model_files = [
            "backend/app/models/__init__.py",
            "backend/app/models/municipality.py",
            "backend/app/models/user.py",
            "backend/app/models/sensor.py",
            "backend/app/models/pipeline.py",
            "backend/app/models/alert.py",
            "backend/app/models/maintenance.py",
            "backend/app/models/device_auth.py",
            "backend/app/models/audit.py",
            "backend/app/models/system.py"
        ]
        
        for file_path in model_files:
            exists = Path(file_path).exists()
            self.print_check(f"Model: {Path(file_path).stem}", exists)
    
    def check_api_endpoints(self):
        """Check API endpoint files."""
        self.print_header("API Endpoints")
        
        api_files = [
            "backend/app/api/auth.py",
            "backend/app/api/sensors.py",
            "backend/app/api/alerts.py",
            "backend/app/api/pipelines.py",
            "backend/app/api/municipalities.py",
            "backend/app/api/incidents.py",
            "backend/app/api/ingest.py",
            "backend/app/api/analytics.py",
            "backend/app/api/admin.py",
            "backend/app/api/monitoring.py"
        ]
        
        for file_path in api_files:
            exists = Path(file_path).exists()
            self.print_check(f"Endpoint: {Path(file_path).stem}", exists)
    
    def check_services(self):
        """Check service layer files."""
        self.print_header("Service Layer")
        
        service_files = [
            "backend/app/services/anomaly_detector.py",
            "backend/app/services/alert_service.py",
            "backend/app/services/notification_service.py",
            "backend/app/services/geospatial_service.py",
            "backend/app/services/analytics_service.py",
            "backend/app/services/cache_service.py",
            "backend/app/services/audit_service.py",
            "backend/app/services/system_health_monitor.py"
        ]
        
        for file_path in service_files:
            exists = Path(file_path).exists()
            self.print_check(f"Service: {Path(file_path).stem}", exists)
    
    def check_middleware(self):
        """Check middleware files."""
        self.print_header("Middleware")
        
        middleware_files = [
            "backend/app/middleware/security.py",
            "backend/app/middleware/rate_limit.py",
            "backend/app/middleware/logging.py"
        ]
        
        for file_path in middleware_files:
            exists = Path(file_path).exists()
            self.print_check(f"Middleware: {Path(file_path).stem}", exists)
    
    def check_frontend_apps(self):
        """Check frontend applications."""
        self.print_header("Frontend Applications")
        
        # Control Room
        control_room_files = [
            "frontend-control-room/package.json",
            "frontend-control-room/src/App.js",
            "frontend-control-room/electron/main.js"
        ]
        
        for file_path in control_room_files:
            exists = Path(file_path).exists()
            self.print_check(f"Control Room: {Path(file_path).name}", exists)
        
        # Mobile App
        mobile_files = [
            "mobile-app/package.json",
            "mobile-app/App.js",
            "mobile-app/screens/DashboardScreen.js",
            "mobile-app/screens/MapScreen.js"
        ]
        
        for file_path in mobile_files:
            exists = Path(file_path).exists()
            self.print_check(f"Mobile App: {Path(file_path).name}", exists)
    
    def check_iot_gateway(self):
        """Check IoT gateway files."""
        self.print_header("IoT Gateway")
        
        iot_files = [
            "iot-gateway/sensor_simulator.py",
            "iot-gateway/multi_protocol_simulator.py",
            "iot-gateway/load_test.py"
        ]
        
        for file_path in iot_files:
            exists = Path(file_path).exists()
            self.print_check(f"IoT: {Path(file_path).name}", exists)
    
    def check_deployment_files(self):
        """Check deployment configuration files."""
        self.print_header("Deployment Configuration")
        
        deployment_files = [
            "docker-compose.yml",
            "backend/Dockerfile",
            "kubernetes/deployment.yaml",
            "kubernetes/production-deployment.yaml"
        ]
        
        for file_path in deployment_files:
            exists = Path(file_path).exists()
            self.print_check(f"Deployment: {Path(file_path).name}", exists)
    
    def check_documentation(self):
        """Check documentation files."""
        self.print_header("Documentation")
        
        doc_files = [
            "README.md",
            "docs/API.md",
            "docs/ARCHITECTURE.md",
            "docs/DEPLOYMENT.md",
            "docs/SECURITY.md",
            "SECURITY_AND_CODE_FIXES_APPLIED.md",
            "PRODUCTION_DEPLOYMENT_CHECKLIST_COMPLETE.md"
        ]
        
        for file_path in doc_files:
            exists = Path(file_path).exists()
            self.print_check(f"Doc: {Path(file_path).name}", exists)
    
    def generate_report(self):
        """Generate final verification report."""
        self.print_header("Verification Summary")
        
        total_checks = len(self.results)
        passed_checks = sum(1 for _, status, _ in self.results if status)
        failed_checks = total_checks - passed_checks
        
        print(f"Total Checks: {total_checks}")
        print(f"{GREEN}Passed: {passed_checks}{RESET}")
        print(f"{RED}Failed: {failed_checks}{RESET}")
        print(f"{YELLOW}Warnings: {len(self.warnings)}{RESET}")
        
        if failed_checks > 0:
            print(f"\n{RED}Failed Checks:{RESET}")
            for name, message in self.errors:
                print(f"  • {name}: {message}")
        
        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for name, message in self.warnings:
                print(f"  • {name}: {message}")
        
        print(f"\n{BOLD}Overall Status:{RESET}")
        if failed_checks == 0:
            print(f"{GREEN}[OK] SYSTEM VERIFICATION PASSED{RESET}")
            print(f"{GREEN}System is ready for deployment!{RESET}")
            return 0
        else:
            print(f"{RED}[FAIL] SYSTEM VERIFICATION FAILED{RESET}")
            print(f"{RED}Please fix the issues above before deployment.{RESET}")
            return 1
    
    def run_all_checks(self):
        """Run all verification checks."""
        print(f"\n{BOLD}National Water Infrastructure Monitoring System{RESET}")
        print(f"{BOLD}System Verification Tool v2.0.0{RESET}")
        
        self.check_python_version()
        self.check_docker()
        self.check_project_structure()
        self.check_required_files()
        self.check_environment_config()
        self.check_database_models()
        self.check_api_endpoints()
        self.check_services()
        self.check_middleware()
        self.check_frontend_apps()
        self.check_iot_gateway()
        self.check_deployment_files()
        self.check_documentation()
        
        return self.generate_report()


def main():
    """Main entry point."""
    verifier = SystemVerifier()
    exit_code = verifier.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
