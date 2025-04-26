from flask import Blueprint, jsonify, request
from app.services import firestore
from app import utils
from werkzeug.security import check_password_hash, generate_password_hash
import time

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Session duration in seconds (e.g., 1 hour)
SESSION_DURATION = 60 * 60

@auth_bp.route('/', methods=['GET'])
def auth_status():
    """
    Simple endpoint to verify the auth route is working
    
    Returns:
        JSON response indicating the auth service is available
    """
    return jsonify({
        'message': 'Auth service is running',
        'status': 'active'
    })

@auth_bp.route('/', methods=['POST'])
def login():
    """
    Authenticate a user using username and password
    
    Expected request body:
    {
        "username": "user_name",
        "password": "user_password"
    }
    
    Returns:
        If successful: JSON with success=1 and session information
        If failed: JSON with success=0 and error message
    """
    # Get JSON data from request
    login_data, error = utils.get_request_data()
    if error:
        return error
    
    # Extract username and password
    username = login_data.get('username')
    password = login_data.get('password')
    
    # Validate input
    if not username or not password:
        return utils.error_response('Username and password are required', 400)
    
    # Query Firestore for user with matching username
    users = firestore.query_documents(
        collection_name='users',
        filters=[('username', '==', username)],
        limit=1
    )
    
    # Check if user exists
    if not users or len(users) == 0:
        return utils.error_response('Invalid username or password', 401)
    
    # Get user record
    user = users[0]
    
    # Check password match
    stored_password_hash = user.get('password')
    
    if not stored_password_hash or not check_password_hash(stored_password_hash, password):
        return utils.error_response('Invalid username or password', 401)
    
    # Authentication successful - create session
    current_time = int(time.time() * 1000)
    expiration_time = current_time + SESSION_DURATION
    
    session_data = {
        'username': username,
        'expires': expiration_time
    }
    
    # Return success response with session information
    return utils.success_response('Authentication successful', {'session': session_data})

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user with username and password
    
    Expected request body:
    {
        "username": "new_user_name",
        "password": "user_password"
    }
    
    Returns:
        If successful: JSON with success=1 and user information
        If failed: JSON with success=0 and error message
    """
    # Get JSON data from request
    registration_data, error = utils.get_request_data()
    if error:
        return error
    
    # Extract username and password
    username = registration_data.get('username')
    password = registration_data.get('password')
    
    # Validate input
    if not username or not password:
        return utils.error_response('Username and password are required', 400)
    
    # Validate password length
    password_error = utils.validate_password(password)
    if password_error:
        return password_error
    
    # Check if username already exists
    existing_users = firestore.query_documents(
        collection_name='users',
        filters=[('username', '==', username)],
        limit=1
    )
    
    if existing_users and len(existing_users) > 0:
        return utils.error_response('Username already exists', 409)  # Conflict status code
    
    # Hash the password
    password_hash = generate_password_hash(password)
    
    # Prepare user data
    user_data = {
        'username': username,
        'password': password_hash,
        'created_at': int(time.time())
    }
    
    # Add user to Firestore
    result = firestore.add_document(
        collection_name='users',
        data=user_data
    )
    
    if not result:
        return utils.error_response('Failed to register user', 500)
    
    # Return success response without password
    user_response = {
        'id': result.get('id'),
        'username': username,
        'created_at': user_data['created_at']
    }
    
    return utils.success_response('Registration successful', {'user': user_response}, 201)