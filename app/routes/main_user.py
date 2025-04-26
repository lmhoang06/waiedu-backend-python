from flask import Blueprint, jsonify, request
from app.models import User
from app.services.postgresql import ensure_db_connection
from app import utils

# Create a blueprint for user management routes
main_user_bp = Blueprint('main_user', __name__, url_prefix='/main/users')

@main_user_bp.route('', methods=['GET'])
@ensure_db_connection
def get_users():
    """
    Retrieve all users.
    
    Query Parameters:
        $select: Comma-separated list of fields to include in the response
        
    Returns:
        JSON response with a list of users.
    """
    # Authenticate the request
    auth_result = utils.authenticate_request()
    if isinstance(auth_result, tuple):
        return auth_result
    
    # Get the $select query parameter
    select_fields = request.args.get('$select', '')
    
    try:
        # Query all users
        users = User.query.all()
        
        # Prepare the response data
        users_data = []
        
        for user in users:
            # Get all available fields except password and sensitive fields
            all_fields = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'birth_date': user.birth_date.isoformat() if user.birth_date else None,
                'gender': user.gender.value if user.gender else None,
                'role': user.role.value,
                'grade': user.grade,
                'school': user.school,
                'teaching_subject': user.teaching_subject,
                'child_grade': user.child_grade,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
            
            # If $select is specified, filter the fields
            if select_fields:
                requested_fields = [field.strip() for field in select_fields.split(',')]
                filtered_data = {field: all_fields[field] for field in requested_fields if field in all_fields}
                
                # Make sure we always include at least the ID
                if 'id' not in filtered_data:
                    filtered_data['id'] = all_fields['id']
                
                user_data = filtered_data
            else:
                # If no selection, return all fields
                user_data = all_fields
            
            users_data.append(user_data)
        
        return utils.success_response('Users retrieved successfully', {'users': users_data})
    
    except Exception as e:
        return utils.error_response(f'Error retrieving users: {str(e)}', 500)

@main_user_bp.route('/<int:user_id>', methods=['GET'])
@ensure_db_connection
def get_user(user_id):
    """
    Retrieve a specific user by ID.
    
    URL Parameters:
        user_id: The ID of the user
        
    Query Parameters:
        $select: Comma-separated list of fields to include in the response
        
    Returns:
        JSON response with the user details.
    """
    # Authenticate the request
    auth_result = utils.authenticate_request()
    if isinstance(auth_result, tuple):
        return auth_result
    
    # Get the $select query parameter
    select_fields = request.args.get('$select', '')
    
    try:
        # Query the user by ID
        user = User.query.get(user_id)
        
        # If user does not exist
        if not user:
            return utils.error_response('User not found', 404)
        
        # All available fields (excluding password and sensitive fields)
        all_fields = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'birth_date': user.birth_date.isoformat() if user.birth_date else None,
            'gender': user.gender.value if user.gender else None,
            'role': user.role.value,
            'grade': user.grade,
            'school': user.school,
            'teaching_subject': user.teaching_subject,
            'child_grade': user.child_grade,
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
        
        # If $select is specified, filter the fields
        if select_fields:
            requested_fields = [field.strip() for field in select_fields.split(',')]
            filtered_data = {field: all_fields[field] for field in requested_fields if field in all_fields}
            
            # Make sure we always include at least the ID
            if 'id' not in filtered_data:
                filtered_data['id'] = all_fields['id']
            
            user_data = filtered_data
        else:
            # If no selection, return all fields
            user_data = all_fields
        
        return utils.success_response('User retrieved successfully', {'user': user_data})
    
    except Exception as e:
        return utils.error_response(f'Error retrieving user: {str(e)}', 500)