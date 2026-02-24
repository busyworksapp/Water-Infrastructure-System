"""Create admin user with direct bcrypt hashing"""
import sys
import os
import bcrypt
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.models.user import User

def create_admin():
    print("🌊 Water Infrastructure - Create Admin User\n")
    
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password (min 8 chars): ").strip()
    full_name = input("Enter admin full name: ").strip()
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        return
    
    db = SessionLocal()
    
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ User with email {email} already exists!")
            return
        
        # Hash password with bcrypt directly
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        
        # Generate username from email
        username = email.split('@')[0]
        
        admin = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=hashed.decode('utf-8'),
            first_name=full_name.split()[0] if full_name else 'Admin',
            last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
            is_active=True,
            is_super_admin=True,
            municipality_id=None
        )
        
        db.add(admin)
        db.commit()
        
        print(f"\n✅ Admin user created successfully!")
        print(f"📧 Email: {email}")
        print(f"👤 Name: {full_name}")
        print(f"🔑 Super Admin: Yes")
        print(f"\n🚀 Login at: https://water-infrastructure-system-production.up.railway.app/docs")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
