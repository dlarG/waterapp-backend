from app import create_app, db
from app.models import Admin, WaterLocation, Barangay, create_default_admin

def initialize_app():
    """Initialize the app with database tables and default data"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("Creating default admin...")
        create_default_admin()
        
        print("✅ App initialized successfully!")
    
    return app

if __name__ == '__main__':
    app = initialize_app()
    print("🚀 Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)