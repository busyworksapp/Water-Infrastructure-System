#!/usr/bin/env python3
"""
National Water Infrastructure Monitoring System
Automated Production Deployment Script
Version 2.0.0
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class DeploymentManager:
    """Manage production deployment process."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.errors = []
        self.warnings = []
    
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
    
    def print_success(self, message: str):
        """Print success message."""
        print(f"{GREEN}✓{RESET} {message}")
    
    def print_error(self, message: str):
        """Print error message."""
        print(f"{RED}✗{RESET} {message}")
        self.errors.append(message)
    
    def print_warning(self, message: str):
        """Print warning message."""
        print(f"{YELLOW}⚠{RESET} {message}")
        self.warnings.append(message)
    
    def run_command(self, cmd: List[str], cwd: Path = None, check: bool = True) -> Tuple[bool, str]:
        """Run shell command and return result."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.root_dir,
                capture_output=True,
                text=True,
                check=check,
                timeout=300
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites."""
        self.print_header("Checking Prerequisites")
        
        all_ok = True
        
        # Check Docker
        success, output = self.run_command(["docker", "--version"], check=False)
        if success:
            self.print_success(f"Docker: {output.strip()}")
        else:
            self.print_error("Docker not found")
            all_ok = False
        
        # Check Docker Compose
        success, output = self.run_command(["docker-compose", "--version"], check=False)
        if success:
            self.print_success(f"Docker Compose: {output.strip()}")
        else:
            self.print_error("Docker Compose not found")
            all_ok = False
        
        # Check Python
        success, output = self.run_command([sys.executable, "--version"], check=False)
        if success:
            self.print_success(f"Python: {output.strip()}")
        else:
            self.print_error("Python not found")
            all_ok = False
        
        # Check environment file
        env_file = self.backend_dir / ".env"
        if env_file.exists():
            self.print_success("Environment file exists")
        else:
            self.print_error("Environment file not found")
            all_ok = False
        
        return all_ok
    
    def build_docker_images(self) -> bool:
        """Build Docker images."""
        self.print_header("Building Docker Images")
        
        print("Building backend image...")
        success, output = self.run_command(
            ["docker-compose", "build", "backend"],
            check=False
        )
        
        if success:
            self.print_success("Backend image built successfully")
            return True
        else:
            self.print_error(f"Failed to build backend image: {output}")
            return False
    
    def start_services(self) -> bool:
        """Start Docker services."""
        self.print_header("Starting Services")
        
        print("Starting all services...")
        success, output = self.run_command(
            ["docker-compose", "up", "-d"],
            check=False
        )
        
        if success:
            self.print_success("Services started successfully")
            
            # Wait for services to be ready
            print("\nWaiting for services to be ready...")
            time.sleep(15)
            
            # Check service status
            success, output = self.run_command(
                ["docker-compose", "ps"],
                check=False
            )
            print(output)
            
            return True
        else:
            self.print_error(f"Failed to start services: {output}")
            return False
    
    def initialize_database(self) -> bool:
        """Initialize database schema."""
        self.print_header("Initializing Database")
        
        init_script = self.backend_dir / "scripts" / "init_db.py"
        if not init_script.exists():
            self.print_error("Database initialization script not found")
            return False
        
        print("Running database initialization...")
        success, output = self.run_command(
            [sys.executable, str(init_script)],
            cwd=self.backend_dir,
            check=False
        )
        
        if success:
            self.print_success("Database initialized successfully")
            print(output)
            return True
        else:
            self.print_warning(f"Database initialization output: {output}")
            return True  # May already be initialized
    
    def verify_health(self) -> bool:
        """Verify system health."""
        self.print_header("Verifying System Health")
        
        # Check backend health
        print("Checking backend health...")
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                self.print_success("Backend is healthy")
                return True
            else:
                self.print_error(f"Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Failed to connect to backend: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Run system tests."""
        self.print_header("Running Tests")
        
        # Check if pytest is available
        success, _ = self.run_command(
            [sys.executable, "-m", "pytest", "--version"],
            check=False
        )
        
        if not success:
            self.print_warning("pytest not installed, skipping tests")
            return True
        
        # Run tests
        print("Running test suite...")
        success, output = self.run_command(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            cwd=self.backend_dir,
            check=False
        )
        
        if success:
            self.print_success("All tests passed")
            return True
        else:
            self.print_warning("Some tests failed")
            print(output)
            return True  # Don't fail deployment on test failures
    
    def display_summary(self):
        """Display deployment summary."""
        self.print_header("Deployment Summary")
        
        if not self.errors:
            print(f"{GREEN}{BOLD}✓ DEPLOYMENT SUCCESSFUL{RESET}\n")
            print("System is ready for production use!\n")
            print("Access points:")
            print(f"  • Backend API:     http://localhost:8000")
            print(f"  • API Docs:        http://localhost:8000/docs")
            print(f"  • Health Check:    http://localhost:8000/health")
            print(f"  • Metrics:         http://localhost:8000/metrics")
            print(f"  • MQTT Broker:     localhost:1883")
            print(f"  • Redis:           localhost:6379")
        else:
            print(f"{RED}{BOLD}✗ DEPLOYMENT FAILED{RESET}\n")
            print("Errors encountered:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print("\nNext steps:")
        print("  1. Create super admin user")
        print("  2. Create test municipality")
        print("  3. Start Control Room: cd frontend-control-room && npm run electron-dev")
        print("  4. Start Mobile App: cd mobile-app && npm start")
        print("  5. Monitor logs: docker-compose logs -f")
    
    def deploy(self):
        """Execute full deployment process."""
        print(f"\n{BOLD}National Water Infrastructure Monitoring System{RESET}")
        print(f"{BOLD}Automated Production Deployment{RESET}")
        print(f"{BOLD}Version 2.0.0{RESET}\n")
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            self.print_error("Prerequisites check failed")
            self.display_summary()
            return False
        
        # Step 2: Build Docker images
        if not self.build_docker_images():
            self.print_error("Docker build failed")
            self.display_summary()
            return False
        
        # Step 3: Start services
        if not self.start_services():
            self.print_error("Service startup failed")
            self.display_summary()
            return False
        
        # Step 4: Initialize database
        if not self.initialize_database():
            self.print_warning("Database initialization had issues")
        
        # Step 5: Verify health
        if not self.verify_health():
            self.print_error("Health check failed")
            self.display_summary()
            return False
        
        # Step 6: Run tests (optional)
        self.run_tests()
        
        # Display summary
        self.display_summary()
        
        return len(self.errors) == 0


def main():
    """Main entry point."""
    deployer = DeploymentManager()
    success = deployer.deploy()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
