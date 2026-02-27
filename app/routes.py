from flask import Blueprint, jsonify, request, send_from_directory
from app import db
from app.models import WaterLocation, Barangay, Admin, Household
from sqlalchemy import text
import json
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

bp = Blueprint('main', __name__)

# Configuration for file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'waterapp-frontend', 'public', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Upload an image for water location"""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"water_location_{timestamp}_{unique_id}.{file_extension}"
            
            # Create upload directory if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Save file
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Return the relative path that will be stored in database
            relative_path = f"images/{filename}"
            
            return jsonify({
                'success': True,
                'message': 'Image uploaded successfully',
                'image_path': relative_path,
                'filename': filename
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'File type not allowed. Please use: PNG, JPG, JPEG, GIF, or WEBP'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500

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

@bp.route('/api/water-locations', methods=['POST'])
def create_water_location():
    """Create a new water location"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['full_name', 'latitude', 'longitude']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Validate coordinates are within reasonable bounds for Maasin
        lat = float(data['latitude'])
        lng = float(data['longitude'])
        
        if not (10.0 <= lat <= 10.3) or not (124.7 <= lng <= 125.1):
            return jsonify({
                'success': False,
                'error': 'Coordinates must be within Maasin City bounds'
            }), 400
          # Create new water location
        location = WaterLocation(
            full_name=data['full_name'].strip(),
            barangay=data.get('barangay'),  # Added barangay field
            latitude=lat,
            longitude=lng,
            coliform_bacteria=data.get('coliform_bacteria'),
            e_coli=data.get('e_coli'),
            image_path=data.get('image_path'),
            sample_date=data.get('sample_date'),
            sample_time=data.get('sample_time'),
            created_by=data.get('created_by')
        )
        
        db.session.add(location)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Water location created successfully',
            'data': location.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'Invalid coordinate values'
        }), 400
    except Exception as e:
        db.session.rollback()
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

@bp.route('/api/barangays/from-locations', methods=['GET'])
def get_barangays_from_locations():
    """Get unique barangays from existing water locations"""
    try:
        # Get unique barangays from water_locations table
        unique_barangays = db.session.execute(text("""
            SELECT DISTINCT barangay 
            FROM water_locations 
            WHERE barangay IS NOT NULL 
            AND barangay != ''
            ORDER BY barangay ASC
        """)).fetchall()
        
        barangay_list = [row[0] for row in unique_barangays if row[0]]
        
        # Add some default Maasin barangays if none exist in database
        default_barangays = [
            "Abgao", "Asuncion", "Batomelong", "Bato", "Batuan",
            "Combado", "Hantag", "Hibatang", "Icot", "Ismerio",
            "Kantagnos", "Katipunan", "Malapoc Norte", "Malapoc Sur",
            "Mantahan", "Matin-ao", "Nonok Norte", "Nonok Sur",
            "Panian", "Poblacion Norte", "Poblacion Sur", "Rizal",
            "San Agustin", "San Isidro", "San Roque", "Santo Niño",
            "Sooc", "Tagnote", "Tagum", "Tomalistis", "Tugas"
        ]
        
        # If no barangays in database, return defaults
        if not barangay_list:
            barangay_list = default_barangays
        
        return jsonify({
            'success': True,
            'data': barangay_list,
            'source': 'database' if unique_barangays else 'default'
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

# 🔧 FIXED: Household endpoints with proper SQL text usage
@bp.route('/api/households', methods=['GET'])
def get_households():
    """Get all households for heatmap visualization"""
    try:
        # 🔧 Use lowercase column names (PostgreSQL converts them automatically)
        households = db.session.execute(text("""
            SELECT 
                longitude,
                latitude,
                q14_toilet_facility,
                barangay_code,
                COUNT(*) as household_count
            FROM household 
            WHERE longitude IS NOT NULL 
            AND latitude IS NOT NULL
            AND longitude BETWEEN 124.7 AND 125.1
            AND latitude BETWEEN 10.0 AND 10.3
            GROUP BY longitude, latitude, q14_toilet_facility, barangay_code
        """)).fetchall()
        
        household_data = []
        for row in households:
            household_data.append({
                'longitude': float(row[0]),  # longitude
                'latitude': float(row[1]),   # latitude
                'toilet_facility': row[2],   # q14_toilet_facility
                'barangay_code': row[3],     # barangay_code
                'household_count': row[4]    # household_count
            })
        
        print(f"🏠 Found {len(household_data)} household clusters")
        
        return jsonify({
            'success': True,
            'data': household_data,
            'total': len(household_data)
        })
    except Exception as e:
        print(f"❌ Error in get_households: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    

@bp.route('/api/households/risk-analysis', methods=['GET'])
def get_household_risk_analysis():
    """Get household risk analysis combining water quality and household density"""
    try:
        # 🔧 FIXED: Use proper boolean comparison (TRUE instead of 1)
        contaminated_locations = db.session.execute(text("""
            SELECT 
                longitude as water_lng,
                latitude as water_lat,
                coliform_bacteria,
                e_coli,
                full_name as location_name
            FROM water_locations 
            WHERE (coliform_bacteria = TRUE OR e_coli = TRUE)
            AND longitude IS NOT NULL 
            AND latitude IS NOT NULL
        """)).fetchall()
        
        print(f"🚨 Found {len(contaminated_locations)} contaminated water sources")
        
        risk_zones = []
        
        for water_source in contaminated_locations:
            print(f"🔍 Analyzing risk around {water_source[4]} at ({water_source[1]}, {water_source[0]})")
            
            households_nearby = db.session.execute(text("""
                SELECT 
                    h.longitude,
                    h.latitude,
                    COUNT(*) as household_count
                FROM household h
                WHERE h.longitude IS NOT NULL 
                AND h.latitude IS NOT NULL
                AND ABS(h.longitude - :water_lng) <= 0.002
                AND ABS(h.latitude - :water_lat) <= 0.002
                GROUP BY h.longitude, h.latitude
                HAVING COUNT(*) > 0
            """), {
                'water_lat': water_source[1],  # water_lat
                'water_lng': water_source[0]   # water_lng
            }).fetchall()
            
            print(f"🏠 Found {len(households_nearby)} household clusters near {water_source[4]}")
            
            for household_cluster in households_nearby:
                risk_score = household_cluster[2]  # household_count
                
                # Calculate risk multiplier
                if water_source[2] and water_source[3]:  # both coliform and e_coli
                    risk_score *= 2.0
                elif water_source[2] or water_source[3]:  # one bacteria present
                    risk_score *= 1.5
                    
                risk_zones.append({
                    'longitude': float(household_cluster[0]),  # longitude
                    'latitude': float(household_cluster[1]),   # latitude
                    'household_count': household_cluster[2],   # household_count
                    'risk_score': risk_score,
                    'water_source': water_source[4],           # location_name
                    'contamination_type': {
                        'coliform': bool(water_source[2]),     # coliform_bacteria
                        'e_coli': bool(water_source[3])        # e_coli
                    }
                })
        
        print(f"🎯 Generated {len(risk_zones)} risk zones")
        
        return jsonify({
            'success': True,
            'data': risk_zones,
            'contaminated_sources': len(contaminated_locations)
        })
    except Exception as e:
        print(f"❌ Error in get_household_risk_analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    

@bp.route('/api/debug/schema', methods=['GET'])
def debug_database_schema():
    """Debug endpoint to check table schemas"""
    try:
        # Check households table structure
        households_schema = db.session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'households'
            ORDER BY ordinal_position
        """)).fetchall()
        
        # Check water_locations table structure  
        water_locations_schema = db.session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'water_locations'
            ORDER BY ordinal_position
        """)).fetchall()
        
        # Count records
        household_count = db.session.execute(text("SELECT COUNT(*) FROM households")).scalar()
        water_location_count = db.session.execute(text("SELECT COUNT(*) FROM water_locations")).scalar()
        contaminated_count = db.session.execute(text("""
            SELECT COUNT(*) FROM water_locations 
            WHERE coliform_bacteria = TRUE OR e_coli = TRUE
        """)).scalar()
        
        return jsonify({
            'success': True,
            'households_schema': [
                {
                    'column': row[0],
                    'type': row[1], 
                    'nullable': row[2]
                } for row in households_schema
            ],
            'water_locations_schema': [
                {
                    'column': row[0],
                    'type': row[1],
                    'nullable': row[2]
                } for row in water_locations_schema
            ],
            'record_counts': {
                'households': household_count,
                'water_locations': water_location_count,
                'contaminated_sources': contaminated_count
            }
        })
        
    except Exception as e:
        print(f"❌ Error in debug_database_schema: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500