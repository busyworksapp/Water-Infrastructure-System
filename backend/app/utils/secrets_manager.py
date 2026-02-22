"""Secure secrets management utility for production deployments."""
import os
import secrets
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class SecretsManager:
    """Manage encrypted secrets for production environments."""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize with master encryption key from environment."""
        self.master_key = master_key or os.getenv("MASTER_ENCRYPTION_KEY")
        if self.master_key:
            self.cipher = self._create_cipher(self.master_key)
        else:
            self.cipher = None
    
    @staticmethod
    def _create_cipher(master_key: str) -> Fernet:
        """Create Fernet cipher from master key."""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'water_monitoring_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return Fernet(key)
    
    def encrypt(self, value: str) -> str:
        """Encrypt a secret value."""
        if not self.cipher:
            raise ValueError("Master encryption key not configured")
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt a secret value."""
        if not self.cipher:
            raise ValueError("Master encryption key not configured")
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    @staticmethod
    def generate_secret_key(length: int = 48) -> str:
        """Generate a cryptographically secure random key."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key."""
        return f"wm_{secrets.token_urlsafe(32)}"
    
    def get_secret(self, key: str, encrypted: bool = False) -> Optional[str]:
        """Get secret from environment, optionally decrypt."""
        value = os.getenv(key)
        if value and encrypted and self.cipher:
            try:
                return self.decrypt(value)
            except Exception:
                return value
        return value


def validate_production_secrets() -> list[str]:
    """Validate that all required secrets are properly configured."""
    errors = []
    
    required_secrets = [
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
    ]
    
    for secret in required_secrets:
        value = os.getenv(secret)
        if not value:
            errors.append(f"Missing required secret: {secret}")
        elif secret == "SECRET_KEY":
            if len(value) < 32:
                errors.append("SECRET_KEY must be at least 32 characters")
            if value in ["change-me", "replace-with-strong-random-secret"]:
                errors.append("SECRET_KEY is using default/example value")
    
    return errors


if __name__ == "__main__":
    # CLI tool for generating secrets
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "generate-key":
            print(f"SECRET_KEY={SecretsManager.generate_secret_key()}")
        
        elif command == "generate-api-key":
            print(f"API_KEY={SecretsManager.generate_api_key()}")
        
        elif command == "validate":
            errors = validate_production_secrets()
            if errors:
                print("❌ Secret validation failed:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)
            else:
                print("✅ All secrets properly configured")
        
        else:
            print("Usage: python secrets_manager.py [generate-key|generate-api-key|validate]")
    else:
        print("Usage: python secrets_manager.py [generate-key|generate-api-key|validate]")
