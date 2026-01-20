from app import create_app, db
from app.models import Admin, WaterLocation, Barangay, create_default_admin

def test_setup():
    """Test the complete setup"""
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            print("Testing database connection...")
            
            # Create default admin
            create_default_admin()
            
            # Test queries
            admin_count = Admin.query.count()
            location_count = WaterLocation.query.count()
            barangay_count = Barangay.query.count()
            
            print(f"✅ Database connected successfully!")
            print(f"   - Admins: {admin_count}")
            print(f"   - Locations: {location_count}")
            print(f"   - Barangays: {barangay_count}")
            
            print("\nDefault admin credentials:")
            print("Username: admin")
            print("Password: admin123")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_setup()