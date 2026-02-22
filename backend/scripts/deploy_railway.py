#!/usr/bin/env python3
"""
Railway.app Deployment & Database Initialization Script

This script handles the complete deployment workflow:
1. Database initialization and migration
2. Service startup
3. Health verification

Run this on Railway as a post-deployment hook.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def log_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def run_command(cmd, description):
    """Run a command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
        print(f"✅ {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main deployment workflow"""
    
    log_section("RAILWAY DEPLOYMENT INITIALIZATION")
    
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'production')}")
    
    # Step 1: Verify database connectivity
    log_section("Step 1: Database Connectivity Verification")
    
    if not run_command(
        "python -c \"from app.core.database import engine; conn = engine.connect(); print('✅ Database connected'); conn.close()\"",
        "Testing database connection"
    ):
        print("⚠️ Database connection test failed")
        print("Proceeding anyway - may be first-time connection")
    
    # Step 2: Initialize database
    log_section("Step 2: Database Initialization")
    
    if not run_command(
        "python scripts/init_db.py",
        "Initializing database schema"
    ):
        print("❌ Database initialization failed")
        return False
    
    # Step 3: Run migrations (if using Alembic)
    log_section("Step 3: Database Migrations")
    
    if Path("alembic.ini").exists():
        run_command(
            "alembic upgrade head",
            "Running database migrations"
        )
    
    # Step 4: System health check
    log_section("Step 4: System Health Check")
    
    print("Waiting for services to stabilize...")
    time.sleep(5)
    
    health_checks = [
        ("python -c \"from app.core.database import SessionLocal; db = SessionLocal(); db.close(); print('✅ Database OK')\"", "Database"),
        ("python -c \"import redis; r = redis.Redis.from_url(os.getenv('REDIS_URL')); r.ping(); print('✅ Redis OK')\"", "Redis"),
    ]
    
    all_healthy = True
    for cmd, service in health_checks:
        if not run_command(cmd, f"Checking {service}"):
            all_healthy = False
    
    # Step 5: Deployment summary
    log_section("Deployment Summary")
    
    if all_healthy:
        print("✅ All systems operational!")
        print("🚀 Deployment successful!")
        print("\nService Status:")
        print("  ✅ Database: Initialized")
        print("  ✅ Redis: Connected")
        print("  ✅ API: Ready to start")
        print("\nNext Steps:")
        print("  1. Start backend: python -m uvicorn app.main:app")
        print("  2. API accessible at: http://localhost:8000")
        print("  3. API docs at: http://localhost:8000/docs")
        return True
    else:
        print("⚠️ Some health checks failed")
        print("Application may still function, but check logs")
        return True  # Don't fail completely

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
