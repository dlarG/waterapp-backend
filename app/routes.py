from flask import Blueprint, jsonify, request
from app import db
from app.models import WaterLocation, Barangay, Admin
import json

bp = Blueprint('main', __name__)

@bp.route('/api/water-locations', methods=['GET'])
def get_water_locations():
    """Get all water monitoring locations"""
    try:
        locations = WaterLocation.query.all()
        return jsonify({
            'success': True,
            'data': [location.to_dict() for location in locations]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/water-locations/<int:location_id>', methods=['GET'])
def get_water_location(location_id):
    """Get specific water location details"""
    try:
        location = WaterLocation.query.get_or_404(location_id)
        return jsonify({
            'success': True,
            'data': location.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/barangays', methods=['GET'])
def get_barangays():
    """Get all barangays in Maasin"""
    try:
        barangays = Barangay.query.all()
        return jsonify({
            'success': True,
            'data': [barangay.to_dict() for barangay in barangays]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/map-bounds', methods=['GET'])
def get_map_bounds():
    """Get map bounds for Maasin, Southern Leyte"""
    # Approximate bounds for Maasin City, Southern Leyte
    bounds = {
        'north': 10.1500,
        'south': 10.0500,
        'east': 125.0500,
        'west': 124.9500,
        'center': {
            'lat': 10.1300,
            'lng': 125.0300
        }
    }
    
    return jsonify({
        'success': True,
        'data': bounds
    })

@bp.route('/api/health', methods=['GET'])
def health_check():
    try:
        admin_count = Admin.query.count()
        location_count = WaterLocation.query.count()
        
        return jsonify({
            'success': True,
            'message': 'Water Monitoring API is running',
            'database': 'connected',
            'stats': {
                'admins': admin_count,
                'locations': location_count
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Database connection failed',
            'error': str(e)
        }), 500

@bp.route('/api/admin/register', methods=['POST'])
def admin_register():
    """Register new admin user"""
    try:
        data = request.get_json()
        full_name = data.get('fullName')  # Changed to match frontend
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not full_name or not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Full name, username, email, and password are required'
            }), 400
        
        # Validate full name
        if len(full_name.strip()) < 2:
            return jsonify({
                'success': False,
                'error': 'Full name must be at least 2 characters'
            }), 400
            
        # Check if username already exists
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            return jsonify({
                'success': False,
                'error': 'Username already exists'
            }), 400
        
        # Check if email already exists  
        existing_email = Admin.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 400
        
        # Create new admin
        new_admin = Admin(
            full_name=full_name.strip(),  # Add full name
            username=username,
            email=email
        )
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Admin account created successfully',
            'admin': new_admin.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    

@bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password required'
            }), 400
        
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password) and admin.is_active == False:
            return jsonify({
                'success': False,
                'error': 'Account waiting for approval. Please contact the system administrator.'
            }), 403
        
        if admin and not admin.check_password(password):
            return jsonify({
                'success': False,
                'error': 'Wrong password. Please try again.'
            }), 403
        
        if admin and admin.check_password(password) and admin.is_active:
            # Update last login
            admin.last_login = db.func.now()
            db.session.commit()
            
            # 🎯 Enhanced response with complete admin data
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'admin': admin.to_dict(),  # Complete admin object
                # Keep these for backward compatibility
                'full_name': admin.full_name,
                'username': admin.username,
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500