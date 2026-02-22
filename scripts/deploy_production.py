#!/usr/bin/env python3
"""Production Deployment Script for Water Monitoring System"""
import os
import sys
import subprocess
import secrets
from pathlib import Path


class ProductionDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
        self.required_vars = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY"]
    
    def check_prerequisites(self):
        print("🔍 Checking prerequisites...")
        try:
            subprocess.run(["railway", "--version"], check=True, capture_output=True)
            print("✅ Railway CLI installed")
        except:
            print("❌ Railway CLI not found. Install: npm install -g @railway/cli")
            return False
        return True
    
    def generate_secret_key(self):
        return secrets.token_urlsafe(48)
    
    def load_env_file(self, env_file=".env.production"):
        env_path = self.backend_dir / env_file
        if not env_path.exists():
            print(f"⚠️  {env_file} not found")
            return {}
        env_vars = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        return env_vars
    
    def validate_environment(self, env_vars):
        print("\n🔍 Validating environment variables...")
        missing = [var for var in self.required_vars if var not in env_vars or not env_vars[var]]
        if missing:
            print(f"❌ Missing: {', '.join(missing)}")
            return False
        secret_key = env_vars.get("SECRET_KEY", "")
        if len(secret_key) < 32 or secret_key in ["change-me", "replace-with-strong-random-secret"]:
            print("❌ SECRET_KEY invalid")
            return False
        print("✅ All required variables present")
        return True
    
    def set_railway_variables(self, env_vars):
        print("\n📤 Setting Railway environment variables...")
        for key, value in env_vars.items():
            if key in self.required_vars or key.startswith(("APP_", "DATABASE_", "REDIS_", "S3_", "MQTT_", "CELERY_")):
                try:
                    subprocess.run(["railway", "variables", "set", f"{key}={value}"], check=True, capture_output=True)
                    print(f"✅ Set {key}")
                except Exception as e:
                    print(f"❌ Failed to set {key}")
                    return False
        return True
    
    def deploy_application(self):
        print("\n🚀 Deploying application...")
        try:
            subprocess.run(["railway", "up"], check=True)
            print("✅ Application deployed")
            return True
        except:
            print("❌ Deployment failed")
            return False
    
    def verify_deployment(self):
        print("\n✅ Verifying deployment...")
        try:
            result = subprocess.run(["railway", "domain"], check=True, capture_output=True, text=True)
            domain = result.stdout.strip()
            if domain:
                print(f"✅ Application: {domain}")
                print(f"📖 API Docs: {domain}/docs")
                return True
            print("⚠️  No domain assigned")
            return False
        except:
            print("❌ Verification failed")
            return False
    
    def run_deployment(self):
        print("=" * 60)
        print("🌊 Water Monitoring System - Production Deployment")
        print("=" * 60)
        
        if not self.check_prerequisites():
            return False
        
        env_vars = self.load_env_file()
        if "SECRET_KEY" not in env_vars or env_vars["SECRET_KEY"] in ["change-me", ""]:
            print("\n🔑 Generating secure SECRET_KEY...")
            env_vars["SECRET_KEY"] = self.generate_secret_key()
        
        if not self.validate_environment(env_vars):
            return False
        
        if not self.set_railway_variables(env_vars):
            return False
        
        if not self.deploy_application():
            return False
        
        self.verify_deployment()
        
        print("\n" + "=" * 60)
        print("✅ Deployment Complete!")
        print("=" * 60)
        return True


def main():
    deployer = ProductionDeployer()
    try:
        success = deployer.run_deployment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Deployment cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
