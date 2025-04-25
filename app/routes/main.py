from flask import Blueprint, jsonify, request
import os
import bcrypt
from app.services import postgresql
from app.services.jwt_service import generate_jwt

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
        # Query database for user with matching email
        query = "SELECT * FROM users WHERE email = :email"
        users = postgresql.execute_query(query, {'email': email})
        
        # Check if user exists
        if not users or len(users) == 0:
            return jsonify({
                'success': 0,
                'message': 'Invalid email or password'
            }), 401
        
        # Get user record
        user = users[0]
        
        # Check password match using bcrypt
        stored_password = user.get('password').encode('utf-8')
        provided_password = password.encode('utf-8')
        
        if not bcrypt.checkpw(provided_password, stored_password):
            return jsonify({
                'success': 0,
                'message': 'Invalid email or password'
            }), 401
        
        # Authentication successful - prepare user data (excluding password)
        user_data = {key: value for key, value in user.items() if key != 'password'}
        
        # Convert keys from snake_case to camelCase
        user_data_camel_case = {}
        for key, value in user_data.items():
            camel_key = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(key.split('_')))
            user_data_camel_case[camel_key] = value
        
        # Get user subjects
        query = """
        SELECT s.id, s.name 
        FROM subjects s
        JOIN user_subjects us ON s.id = us.subject_id
        WHERE us.user_id = :user_id
        """
        subjects = postgresql.execute_query(query, {'user_id': user['id']})
        
        # Convert subject keys from snake_case to camelCase
        subjects_camel_case = []
        for subject in subjects:
            subject_camel_case = {}
            for key, value in subject.items():
                camel_key = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(key.split('_')))
                subject_camel_case[camel_key] = value
            subjects_camel_case.append(subject_camel_case)
        
        # Add subjects to user data if any found
        if subjects_camel_case:
            user_data_camel_case['subjects'] = subjects_camel_case
        
        # Generate JWT token
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')
        token = generate_jwt({'userId': user['id'], 'email': user['email']}, jwt_secret)
        
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
        # Check if email already exists
        query = "SELECT id FROM users WHERE email = :email"
        existing_user = postgresql.execute_query(query, {'email': email})
        
        if existing_user and len(existing_user) > 0:
            return jsonify({
                'success': 0,
                'message': 'Email already registered'
            }), 409
        
        # Hash the password with bcrypt
        salt = bcrypt.gensalt(rounds=10)  # Salt rounds = 10
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Create user data object from registration_data, replacing password with hashed version
        user_data = {
            'name': name,
            'email': email,
            'password': hashed_password.decode('utf-8'),
            'role': role,
            'is_verified': False
        }
        
        # Add optional fields if they exist
        if phone:
            user_data['phone'] = phone
        if birth_date:
            user_data['birth_date'] = birth_date
        if gender:
            user_data['gender'] = gender
        if grade:
            user_data['grade'] = grade
        if school:
            user_data['school'] = school
        if teaching_subject:
            user_data['teaching_subject'] = teaching_subject
        if child_grade:
            user_data['child_grade'] = child_grade
            
        # Generate verification token
        import uuid
        verification_token = str(uuid.uuid4())
        user_data['verification_token'] = verification_token
        
        try:
            # Insert the new user
            columns = ', '.join(user_data.keys())
            placeholders = ', '.join([f':{key}' for key in user_data.keys()])
            
            insert_query = f"""
            INSERT INTO users ({columns}) 
            VALUES ({placeholders})
            RETURNING id, name, email, role, is_verified, created_at, updated_at
            """
            
            result = postgresql.execute_query(insert_query, user_data)
            
            if not result or len(result) == 0:
                return jsonify({
                    'success': 0,
                    'message': 'Failed to create user'
                }), 500
                
            user_id = result[0]['id']
            
            # Insert interested subjects if any
            if interested_subjects and isinstance(interested_subjects, list) and len(interested_subjects) > 0:
                # Process each subject separately with postgresql.execute_query
                for subject_id in interested_subjects:
                    try:
                        # Use simple INSERT query without expecting results back
                        subject_query = """
                        INSERT INTO user_subjects (user_id, subject_id) 
                        VALUES (:user_id, :subject_id)
                        """
                        
                        # Using execute_non_query or a method that doesn't expect results
                        # If postgresql has no specific method for non-query operations, add RETURNING clause
                        postgresql.execute_query(subject_query + " RETURNING 1", {
                            'user_id': user_id,
                            'subject_id': subject_id
                        })
                    except Exception as subject_error:
                        # Log error but continue with other subjects
                        print(f"Error adding subject {subject_id}: {str(subject_error)}")
            
            # Convert keys from snake_case to camelCase
            user_data_camel_case = {}
            for key, value in result[0].items():
                camel_key = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(key.split('_')))
                user_data_camel_case[camel_key] = value
            
            # Generate JWT token
            jwt_secret = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')
            token = generate_jwt({
                'userId': user_id, 
                'email': result[0]['email'],
                'role': result[0]['role']
            }, jwt_secret)
            
            # Here you would send verification email to the user
            # send_verification_email(email, verification_token)
            
            # Return success response
            return jsonify({
                'success': 1,
                'message': 'Registration successful',
                'token': token,
                'user': user_data_camel_case
            }), 201
                
        except Exception as e:
            raise e
        
    except Exception as e:
        return jsonify({
            'success': 0,
            'message': f'Error during registration: {str(e)}'
        }), 500

