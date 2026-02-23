#!/usr/bin/env python3
"""
Create first super admin user for Water Infrastructure Monitoring System
"""
import requests
import json

# Your Railway API URL
API_URL = "https://water-infrastructure-system-production.up.railway.app"

def create_admin_user():
    """Create the first super admin user"""
    
    print("🌊 Water Infrastructure Monitoring System - Admin Setup\n")
    
    # Get user input
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password (min 8 chars): ").strip()
    full_name = input("Enter admin full name: ").strip()
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        return
    
    # Create municipality first (required for user)
    print("\n📍 Creating default municipality...")
    municipality_data = {
        "name": "National Water Authority",
        "code": "NWA001",
        "region": "National",
        "contact_email": email,
        "contact_phone": "+1234567890"
    }
    
    try:
        # Note: This endpoint might require authentication
        # You may need to create municipality directly in database
        print("⚠️  Municipality creation may require database access")
        print("   Use the /docs endpoint to create municipality first if needed\n")
    except Exception as e:
        print(f"Note: {e}\n")
    
    # Create super admin user
    print("👤 Creating super admin user...")
    user_data = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "is_super_admin": True,
        "is_active": True
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Admin user created successfully!\n")
            print("📧 Email:", email)
            print("🔑 You can now login at /docs\n")
            
            # Try to login
            print("🔐 Testing login...")
            login_response = requests.post(
                f"{API_URL}/api/v1/auth/login",
                data={
                    "username": email,
                    "password": password
                }
            )
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                print("✅ Login successful!")
                print(f"\n🎫 Access Token (save this):\n{token_data.get('access_token')}\n")
            else:
                print(f"⚠️  Login test failed: {login_response.text}")
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Alternative: Use the API docs at /docs to create user manually")

if __name__ == "__main__":
    create_admin_user()
