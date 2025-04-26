"""
Utility functions for the application
"""
from flask import jsonify, request
import bcrypt
import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, Union
from app.services.postgresql import db
from app.models.user import User

# Constants
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MIN_PASSWORD_LENGTH = 8


def get_request_data() -> Tuple[Dict[str, Any], Optional[Tuple]]:
    """
    Get and validate JSON data from request
    
    Returns:
        Tuple containing:
        - Dictionary with request data
        - Tuple with error response or None if no error
    """
    data = request.get_json()
    
    if not data:
        return {}, (jsonify({
            'success': 0,
            'message': 'No data provided'
        }), 400)
    
    return data, None


def validate_email(email: str) -> Optional[Tuple]:
    """
    Validate email format
    
    Args:
        email: Email to validate
    
    Returns:
        Tuple with error response or None if valid
    """
    if not email:
        return jsonify({
            'success': 0,
            'message': 'Email is required'
        }), 400
    
    if not re.match(EMAIL_REGEX, email):
        return jsonify({
            'success': 0,
            'message': 'Invalid email format'
        }), 400
    
    return None


def validate_password(password: str, confirm_password: str = None) -> Optional[Tuple]:
    """
    Validate password
    
    Args:
        password: Password to validate
        confirm_password: Optional confirmation password to compare
    
    Returns:
        Tuple with error response or None if valid
    """
    if not password:
        return jsonify({
            'success': 0,
            'message': 'Password is required'
        }), 400
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({
            'success': 0,
            'message': f'Password must be at least {MIN_PASSWORD_LENGTH} characters long'
        }), 400
    
    if confirm_password is not None and password != confirm_password:
        return jsonify({
            'success': 0,
            'message': 'Passwords do not match'
        }), 400
    
    return None


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt(rounds=10)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def serialize_user(user: User, include_subjects: bool = True) -> Dict[str, Any]:
    """
    Convert a User model to a dictionary for JSON serialization
    
    Args:
        user: User model instance
        include_subjects: Whether to include user subjects
    
    Returns:
        Dictionary with user data in camelCase format
    """
    # Convert SQLAlchemy model to dictionary (excluding password)
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
    
    # Include subjects if requested
    if include_subjects and user.user_subjects:
        subjects_data = []
        for user_subject in user.user_subjects:
            subject = user_subject.subject
            subjects_data.append({
                'id': subject.id,
                'name': subject.name
            })
        
        if subjects_data:
            user_data_camel_case['subjects'] = subjects_data
    
    return user_data_camel_case


def success_response(message: str, data: Dict[str, Any] = None, status_code: int = 200) -> Tuple:
    """
    Create a success response
    
    Args:
        message: Success message
        data: Additional data for the response
        status_code: HTTP status code
    
    Returns:
        Tuple containing JSON response and status code
    """
    response = {
        'success': 1,
        'message': message
    }
    
    if data:
        response.update(data)
    
    return jsonify(response), status_code


def error_response(message: str, status_code: int = 400) -> Tuple:
    """
    Create an error response
    
    Args:
        message: Error message
        status_code: HTTP status code
    
    Returns:
        Tuple containing JSON response and status code
    """
    return jsonify({
        'success': 0,
        'message': message
    }), status_code