from app import db
from datetime import datetime, date, time
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, Date, Time
from werkzeug.security import generate_password_hash, check_password_hash

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    def __repr__(self):
        return f'<Admin {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class WaterLocation(db.Model):
    __tablename__ = 'water_locations'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    
    # Simple coordinates without PostGIS
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Water quality data
    coliform_bacteria = Column(Boolean, nullable=True)
    e_coli = Column(Boolean, nullable=True)

    # Image path
    image_path = Column(String(255), nullable=True)
    
    # Date and time
    sample_date = Column(Date, nullable=True)
    sample_time = Column(Time, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, db.ForeignKey('admins.id'), nullable=True)
    
    # Relationships
    admin = db.relationship('Admin', backref='water_locations')
    
    @property
    def water_status(self):
        """Compute water status based on bacteria presence"""
        if self.coliform_bacteria and self.e_coli:
            return "hazard"
        elif self.coliform_bacteria or self.e_coli:
            return "undrinkable"
        else:
            return "safe"
    
    def __repr__(self):
        return f'<WaterLocation {self.full_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'coliform_bacteria': self.coliform_bacteria,
            'e_coli': self.e_coli,
            'water_status': self.water_status,
            'image_path': self.image_path,
            'sample_date': self.sample_date.isoformat() if self.sample_date else None,
            'sample_time': self.sample_time.isoformat() if self.sample_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

class Barangay(db.Model):
    __tablename__ = 'barangays'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Center coordinates for map focus (without PostGIS)
    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Barangay {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'center_latitude': float(self.center_latitude) if self.center_latitude else None,
            'center_longitude': float(self.center_longitude) if self.center_longitude else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Helper function to create default admin
def create_default_admin():
    """Create default admin user if none exists"""
    if not Admin.query.first():
        admin = Admin(
            username='admin',
            full_name='System Administrator',
            email='admin@watermonitor.com'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: username='admin', password='admin123'")