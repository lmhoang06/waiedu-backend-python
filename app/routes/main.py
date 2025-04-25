from flask import Blueprint, jsonify, request
import os
import bcrypt
import re
import uuid
from app.services import postgresql
from app.services.jwt_service import generate_jwt
from app.models.user import User
from app.models.subject import Subject
from app.models.user_subject import UserSubject
from app.models.enums import UserGender, UserRole
from app.services.postgresql import db

# Create a blueprint for main routes
main_bp = Blueprint('main', __name__, url_prefix='/main')

@main_bp.route('/', methods=['GET'])
def index():
    """
    Root endpoint for the main blueprint
    
    Returns:
        JSON response indicating the main service is available
    """
    return jsonify({
        'message': 'Main service is running',
        'status': 'active'
    })

@main_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Authenticate a user with email and password
    
    Expected request body:
    {
        "email": "user@example.com",
        "password": "userpassword"
    }
    
    Returns:
        If successful: JSON with success=1, token and user data
        If failed: JSON with success=0 and error message
    """
    # Get JSON data from request
    login_data = request.get_json()
    
    if not login_data:
        return jsonify({
            'success': 0,
            'message': 'No data provided'
        }), 400
    
    # Extract email and password
    email = login_data.get('email')
    password = login_data.get('password')
    
    # Validate input
    if not email or not password:
        return jsonify({
            'success': 0,
            'message': 'Email and password are required'
        }), 400
    
    try:
        # Query database for user with matching email using SQLAlchemy model
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists
        if not user:
            return jsonify({
                'success': 0,
                'message': 'Invalid email or password'
            }), 401
        
        # Check password match using bcrypt
        stored_password = user.password.encode('utf-8')
        provided_password = password.encode('utf-8')
        
        if not bcrypt.checkpw(provided_password, stored_password):
            return jsonify({
                'success': 0,
                'message': 'Invalid email or password'
            }), 401
        
        # Authentication successful - prepare user data (excluding password)
        # Convert SQLAlchemy model to dictionary
        user_data = {column.name: getattr(user, column.name) 
                    for column in User.__table__.columns 
                    if column.name != 'password'}
        
        # Handle date and enum types for JSON serialization
        for key, value in user_data.items():
            if key == 'birth_date' and value is not None:
                user_data[key] = value.isoformat()
            elif key == 'gender' and value is not None:
                user_data[key] = value.value
            elif key == 'role':
                user_data[key] = value.value
            elif key in ['created_at', 'updated_at'] and value is not None:
                user_data[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
        
        # Convert keys from snake_case to camelCase
        user_data_camel_case = {}
        for key, value in user_data.items():
            camel_key = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(key.split('_')))
            user_data_camel_case[camel_key] = value
        
        # Get user subjects using the relationship
        subjects_data = []
        if user.user_subjects:
            for user_subject in user.user_subjects:
                subject = user_subject.subject
                subjects_data.append({
                    'id': subject.id,
                    'name': subject.name
                })
        
        # Add subjects to user data if any found
        if subjects_data:
            user_data_camel_case['subjects'] = subjects_data
        
        # Generate JWT token
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')
        token = generate_jwt({'userId': user.id, 'email': user.email}, jwt_secret)
        
        # Return success response
        return jsonify({
            'success': 1,
            'message': 'Authentication successful',
            'token': token,
            'user': user_data_camel_case
        })
        
    except Exception as e:
        return jsonify({
            'success': 0,
            'message': f'Error during authentication: {str(e)}'
        }), 500

@main_bp.route('/auth/register', methods=['POST'])
def register():
    """
    Register a new user with email and password
    
    Expected request body:
    {
        "email": "user@example.com",
        "password": "userpassword",
        "name": "User Name",
        "role": "student|teacher|parent",
        ... (other user fields)
    }
    
    Returns:
        If successful: JSON with success=1 and user data
        If failed: JSON with success=0 and error message
    """
    # Get JSON data from request
    registration_data = request.get_json()
    
    if not registration_data:
        return jsonify({
            'success': 0,
            'message': 'No data provided'
        }), 400
    
    # Extract required fields
    email = registration_data.get('email')
    password = registration_data.get('password')
    name = registration_data.get('name')
    role = registration_data.get('role', 'student')  # Default to student if not provided
    
    # Validate input
    if not email or not password or not name:
        return jsonify({
            'success': 0,
            'message': 'Email, password, and name are required'
        }), 400
    
    # Validate email format using a simple regex
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return jsonify({
            'success': 0,
            'message': 'Invalid email format'
        }), 400
    
    # Validate password length
    if len(password) < 8:
        return jsonify({
            'success': 0,
            'message': 'Password must be at least 8 characters long'
        }), 400
    
    # Validate role enum
    if role not in ['student', 'teacher', 'parent']:
        return jsonify({
            'success': 0,
            'message': 'Role must be one of: student, teacher, parent'
        }), 400
    
    # Extract optional fields
    phone = registration_data.get('phone')
    birth_date = registration_data.get('birthDate')
    gender = registration_data.get('gender')
    grade = registration_data.get('grade')
    school = registration_data.get('school')
    teaching_subject = registration_data.get('teachingSubject')
    child_grade = registration_data.get('childGrade')
    interested_subjects = registration_data.get('interestedSubjects', [])
    
    try:
        # Check if email already exists using SQLAlchemy model
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            return jsonify({
                'success': 0,
                'message': 'Email already registered'
            }), 409
        
        # Hash the password with bcrypt
        salt = bcrypt.gensalt(rounds=10)  # Salt rounds = 10
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Convert the role string to UserRole enum
        user_role = UserRole[role]
        
        # Convert the gender string to UserGender enum if provided
        user_gender = None
        if gender:
            try:
                user_gender = UserGender[gender]
            except KeyError:
                return jsonify({
                    'success': 0,
                    'message': 'Invalid gender value'
                }), 400
        
        # Create new User instance
        new_user = User(
            name=name,
            email=email,
            password=hashed_password.decode('utf-8'),
            role=user_role,
            is_verified=False,
            verification_token=str(uuid.uuid4())
        )
        
        # Add optional fields if they exist
        if phone:
            new_user.phone = phone
        if birth_date:
            new_user.birth_date = birth_date
        if user_gender:
            new_user.gender = user_gender
        if grade:
            new_user.grade = grade
        if school:
            new_user.school = school
        if teaching_subject:
            new_user.teaching_subject = teaching_subject
        if child_grade:
            new_user.child_grade = child_grade
            
        # Add the user to the session and commit to get the ID
        db.session.add(new_user)
        db.session.flush()  # This assigns an ID without committing the transaction
        
        # Add interested subjects if any
        if interested_subjects and isinstance(interested_subjects, list) and len(interested_subjects) > 0:
            for subject_id in interested_subjects:
                # Check if subject exists
                subject = Subject.query.get(subject_id)
                if subject:
                    # Create UserSubject association
                    user_subject = UserSubject(
                        user_id=new_user.id,
                        subject_id=subject_id
                    )
                    db.session.add(user_subject)
        
        # Commit the transaction to save all changes
        db.session.commit()
        
        # Prepare user data for response (excluding password)
        user_data = {column.name: getattr(new_user, column.name) 
                    for column in User.__table__.columns 
                    if column.name != 'password'}
        
        # Handle date and enum types for JSON serialization
        for key, value in user_data.items():
            if key == 'birth_date' and value is not None:
                user_data[key] = value.isoformat()
            elif key == 'gender' and value is not None:
                user_data[key] = value.value
            elif key == 'role':
                user_data[key] = value.value
            elif key in ['created_at', 'updated_at'] and value is not None:
                user_data[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
        
        # Convert keys from snake_case to camelCase
        user_data_camel_case = {}
        for key, value in user_data.items():
            camel_key = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(key.split('_')))
            user_data_camel_case[camel_key] = value
        
        # Get user subjects if any were added
        subjects_data = []
        if new_user.user_subjects:
            for user_subject in new_user.user_subjects:
                subject = user_subject.subject
                subjects_data.append({
                    'id': subject.id,
                    'name': subject.name
                })
        
        # Add subjects to user data if any found
        if subjects_data:
            user_data_camel_case['subjects'] = subjects_data
        
        # Generate JWT token
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')
        token = generate_jwt({
            'userId': new_user.id, 
            'email': new_user.email,
            'role': new_user.role.value
        }, jwt_secret)
        
        # Here you would send verification email to the user
        # send_verification_email(email, new_user.verification_token)
        
        # Return success response
        return jsonify({
            'success': 1,
            'message': 'Registration successful',
            'token': token,
            'user': user_data_camel_case
        }), 201
                
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        return jsonify({
            'success': 0,
            'message': f'Error during registration: {str(e)}'
        }), 500

