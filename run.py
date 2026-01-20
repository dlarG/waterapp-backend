from app import create_app, db
from app.models import Admin, WaterLocation, Barangay, create_default_admin

app = create_app()

@app.before_first_request
def create_tables():
    """Create database tables and default admin"""
    db.create_all()
    create_default_admin()

if __name__ == '__main__':
    app.run(debug=True)