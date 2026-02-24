"""
Create Super Admin User
Run this script to create the first admin user in the database
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin():
    print("🌊 Water Infrastructure - Create Admin User\n")
    
    # Get user input
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password (min 8 chars): ").strip()
    full_name = input("Enter admin full name: ").strip()
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        return
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ User with email {email} already exists!")
            return
        
        # Create admin user
        admin = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_super_admin=True,
            municipality_id=None  # Super admin has no municipality restriction
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"\n✅ Admin user created successfully!")
        print(f"📧 Email: {email}")
        print(f"👤 Name: {full_name}")
        print(f"🔑 Super Admin: Yes")
        print(f"\n🚀 You can now login at:")
        print(f"   https://water-infrastructure-system-production.up.railway.app/docs")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
