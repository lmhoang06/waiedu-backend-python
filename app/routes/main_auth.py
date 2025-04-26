from flask import Blueprint, jsonify
import os
import uuid
from datetime import datetime, timedelta
from app.services.jwt_service import generate_jwt
from app.models import User, Subject, UserSubject, UserGender, UserRole
from app.services.postgresql import db
from app import utils

# Create a blueprint for main routes
main_auth_bp = Blueprint('main', __name__, url_prefix='/main/auth')

@main_auth_bp.route('/login', methods=['POST'])
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
    login_data, error = utils.get_request_data()
    if error:
        return error
    
    # Extract email and password
    email = login_data.get('email')
    password = login_data.get('password')
    
    # Validate input
    if not email or not password:
        return utils.error_response('Email and password are required', 400)
    
    try:
        # Query database for user with matching email using SQLAlchemy model
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists
        if not user:
            return utils.error_response('Invalid email or password', 401)
        
        # Check password match using bcrypt
        if not utils.verify_password(password, user.password):
            return utils.error_response('Invalid email or password', 401)
        
        # Serialize user data
        user_data = utils.serialize_user(user)
        
        # Generate JWT token
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')
        token = generate_jwt({'userId': user.id, 'email': user.email}, jwt_secret)
        
        # Return success response
        return utils.success_response(
            'Authentication successful',
            {'token': token, 'user': user_data}
        )
        
    except Exception as e:
        return utils.error_response(f'Error during authentication: {str(e)}', 500)

@main_auth_bp.route('/register', methods=['POST'])
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
    registration_data, error = utils.get_request_data()
    if error:
        return error
    
    # Extract required fields
    email = registration_data.get('email')
    password = registration_data.get('password')
    name = registration_data.get('name')
    role = registration_data.get('role', 'student')  # Default to student if not provided
    
    # Validate input
    if not name:
        return utils.error_response('Name is required', 400)
        
    # Validate email
    email_error = utils.validate_email(email)
    if email_error:
        return email_error
    
    # Validate password
    password_error = utils.validate_password(password)
    if password_error:
        return password_error
    
    # Validate role enum
    if role not in ['student', 'teacher', 'parent']:
        return utils.error_response('Role must be one of: student, teacher, parent', 400)
    
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
            return utils.error_response('Email already registered', 409)
        
        # Convert the role string to UserRole enum
        user_role = UserRole[role]
        
        # Convert the gender string to UserGender enum if provided
        user_gender = None
        if gender:
            try:
                user_gender = UserGender[gender]
            except KeyError:
                return utils.error_response('Invalid gender value', 400)
        
        # Create new User instance
        new_user = User(
            name=name,
            email=email,
            password=utils.hash_password(password),
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
        
        # Serialize user data
        user_data = utils.serialize_user(new_user)
        
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
        return utils.success_response(
            'Registration successful',
            {'token': token, 'user': user_data}, 
            201
        )
                
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        return utils.error_response(f'Error during registration: {str(e)}', 500)

@main_auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Process forgot password request and generate reset token
    
    Expected request body:
    {
        "email": "user@example.com"
    }
    
    Returns:
        JSON response with status and message
    """
    # Get JSON data from request
    data, error = utils.get_request_data()
    if error:
        return error
    
    # Extract email
    email = data.get('email')
    
    # Validate email
    email_error = utils.validate_email(email)
    if email_error:
        return email_error
    
    try:
        # Check if user exists with the given email
        user = User.query.filter_by(email=email).first()
        
        # For security reasons, we return the same message whether the email exists or not
        # to prevent user enumeration attacks
        
        # If user exists, generate token and update user record
        if user:
            # Generate a reset token
            reset_token = str(uuid.uuid4())
            
            # Set expiry time (24 hours from now)
            reset_token_expiry = datetime.now() + timedelta(hours=24)
            
            # Update the user record
            user.reset_token = reset_token
            user.reset_token_expiry = reset_token_expiry
            db.session.commit()
            
            # In a real application, send email with reset link
            # send_reset_email(email, reset_token)
            
            # Debug info for development - remove in production
            debug_info = {'debug_token': reset_token} if os.environ.get('FLASK_ENV') == 'development' else {}
        else:
            debug_info = {}
        
        # Return success response
        response = {
            'success': 1,
            'message': 'If an account with this email exists, a reset link has been sent.'
        }
        
        # Add debug info if available
        response.update(debug_info)
        
        return jsonify(response)
        
    except Exception as e:
        # Log the error (ideally to a proper logging system)
        print(f"Error processing forgot password request: {str(e)}")
        
        # Rollback transaction in case of error
        db.session.rollback()
        
        return utils.error_response('Request failed. Please try again later.', 500)

@main_auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset user password using token
    
    Expected request body:
    {
        "token": "reset_token_uuid",
        "password": "newpassword",
        "confirmPassword": "newpassword"
    }
    
    Returns:
        JSON response with status and message
    """
    # Get JSON data from request
    data, error = utils.get_request_data()
    if error:
        return error
    
    # Extract required fields
    token = data.get('token')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')
    
    # Validate required fields
    if not token:
        return utils.error_response('Token is required')
    
    # Validate password
    password_error = utils.validate_password(password, confirm_password)
    if password_error:
        return password_error
    
    try:
        # Find user with valid reset token
        user = User.query.filter(
            User.reset_token == token,
            User.reset_token_expiry > datetime.now()
        ).first()
        
        if not user:
            return utils.error_response('Invalid or expired token', 400)
        
        # Update the user's password and clear reset token fields
        user.password = utils.hash_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        
        # Commit the changes
        db.session.commit()
        
        # Return success response
        return utils.success_response('Password has been reset successfully')
        
    except Exception as e:
        # Log the error
        print(f"Error resetting password: {str(e)}")
        
        # Rollback the transaction in case of error
        db.session.rollback()
        
        return utils.error_response('Password reset failed. Please try again later.', 500)

