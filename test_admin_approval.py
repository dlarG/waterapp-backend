#!/usr/bin/env python3
"""
Test script to verify admin registration requires approval
"""
from app import create_app, db
from app.models import Admin

def test_admin_registration():
    app = create_app()
    
    with app.app_context():
        # Test 1: Check that new Admin instances have is_active=False by default
        print("🧪 Testing Admin model default values...")
        
        test_admin = Admin(
            username='test_user',
            full_name='Test User',
            email='test@example.com'
        )
        test_admin.set_password('password123')
        
        # Check default value
        assert test_admin.is_active == False, f"❌ Expected is_active=False, got {test_admin.is_active}"
        print("✅ Admin model defaults to is_active=False")
        
        # Test 2: Verify that explicitly setting is_active=True works
        print("\n🧪 Testing explicit is_active=True...")
        
        active_admin = Admin(
            username='active_user',
            full_name='Active User', 
            email='active@example.com',
            is_active=True
        )
        active_admin.set_password('password123')
        
        assert active_admin.is_active == True, f"❌ Expected is_active=True, got {active_admin.is_active}"
        print("✅ Explicit is_active=True works correctly")
        
        # Test 3: Check default admin creation
        print("\n🧪 Testing default admin creation...")
        
        # Clear any existing admins for clean test
        Admin.query.delete()
        db.session.commit()
        
        from app.models import create_default_admin
        create_default_admin()
        
        default_admin = Admin.query.filter_by(username='admin').first()
        assert default_admin is not None, "❌ Default admin was not created"
        assert default_admin.is_active == True, f"❌ Default admin should be active, got {default_admin.is_active}"
        print("✅ Default admin is created as active")
        
        print(f"\n🎉 All tests passed!")
        print(f"📋 Summary:")
        print(f"   • New admin accounts default to is_active=False (require approval)")
        print(f"   • Default 'admin' account is created as active") 
        print(f"   • Explicit is_active=True still works for special cases")

if __name__ == '__main__':
    test_admin_registration()
