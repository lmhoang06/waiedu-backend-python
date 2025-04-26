from flask import Blueprint, jsonify, request
from app.services.postgresql import ensure_db_connection
from app import utils
from app.models import User, UserSubject, Subject
from app.services.postgresql import ensure_db_connection, db
from app.models.enums import UserRole, UserGender
from functools import wraps

# Create a blueprint for user management routes
main_user_bp = Blueprint('main_user', __name__, url_prefix='/main/users')

def owner_required(f):
    """
    Decorator to ensure that only the account owner or an admin can access these routes
    
    Returns:
        Decorated function that checks user permissions before execution
    """
    @wraps(f)
    def decorated_function(user_id, *args, **kwargs):
        # Authenticate the request
        auth_result = utils.authenticate_request()
        if isinstance(auth_result, tuple):
            return auth_result
            
        # Get the authenticated user
        current_user = auth_result
        
        # Check if user is the owner of the account or an admin
        if current_user.id != user_id:
            return utils.error_response('Permission denied. You can only modify your own account.', 403)
            
        # Pass the authenticated user to the route function
        return f(current_user, user_id, *args, **kwargs)
    return decorated_function

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

@main_user_bp.route('/<int:user_id>', methods=['PUT', 'PATCH'])
@ensure_db_connection
@owner_required
def update_user(current_user, user_id):
    """
    Update a specific user by ID. Only the account owner or an admin can update an account.
    
    URL Parameters:
        user_id: The ID of the user to update
        
    Expected request body:
    {
        "name": "Updated Name",
        "phone": "1234567890",
        ... (other fields to update)
    }
    
    Returns:
        JSON response with the updated user details.
    """
    # Get JSON data from request
    update_data, error = utils.get_request_data()
    if error:
        return error
    
    try:
        # Query the user by ID
        user = User.query.get(user_id)
        
        # If user does not exist
        if not user:
            return utils.error_response('User not found', 404)
        
        # Update fields if they exist in the request
        if 'name' in update_data:
            user.name = update_data['name']
            
        if 'phone' in update_data:
            user.phone = update_data['phone']
            
        if 'grade' in update_data:
            user.grade = update_data['grade']
            
        if 'school' in update_data:
            user.school = update_data['school']
            
        if 'teaching_subject' in update_data:
            user.teaching_subject = update_data['teaching_subject']
            
        if 'child_grade' in update_data:
            user.child_grade = update_data['child_grade']
            
        if 'gender' in update_data:
            gender = update_data['gender']
            if gender:
                try:
                    user.gender = UserGender[gender]
                except KeyError:
                    return utils.error_response('Invalid gender value', 400)
            else:
                user.gender = None
        
        # Handle email updates - only if current user is admin or it's verified first
        if 'email' in update_data and (current_user.role == UserRole.admin or user.is_verified):
            email = update_data['email']
            
            # Validate email
            email_error = utils.validate_email(email)
            if email_error:
                return email_error
                
            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user_id:
                return utils.error_response('Email already registered', 409)
                
            user.email = email
            # If email was changed, set verified to false
            if user.email != email:
                user.is_verified = False
        
        # Handle password updates - needs current password and new password
        if 'password' in update_data:
            if 'current_password' not in update_data:
                return utils.error_response('Current password is required to update password', 400)
                
            # Verify current password
            if not utils.verify_password(update_data['current_password'], user.password):
                return utils.error_response('Current password is incorrect', 401)
                
            # Validate new password
            password_error = utils.validate_password(update_data['password'], update_data.get('confirm_password'))
            if password_error:
                return password_error
                
            # Hash and set new password
            user.password = utils.hash_password(update_data['password'])
            
        # Handle interested subjects updates
        if 'interested_subjects' in update_data:
            interested_subjects = update_data['interested_subjects']
            
            if interested_subjects and isinstance(interested_subjects, list):
                # Remove existing user_subjects
                UserSubject.query.filter_by(user_id=user.id).delete()
                
                # Add new user_subjects
                for subject_id in interested_subjects:
                    subject = Subject.query.get(subject_id)
                    if subject:
                        user_subject = UserSubject(
                            user_id=user.id,
                            subject_id=subject_id
                        )
                        db.session.add(user_subject)
        
        # Save changes to database
        db.session.commit()
        
        # Return the updated user data
        user_data = utils.serialize_user(user)
        if 'verificationToken' in user_data:
            del user_data['verificationToken']
        return utils.success_response('User updated successfully', {'user': user_data})
        
    except Exception as e:
        db.session.rollback()
        return utils.error_response(f'Error updating user: {str(e)}', 500)

@main_user_bp.route('/<int:user_id>', methods=['DELETE'])
@ensure_db_connection
@owner_required
def delete_user(current_user, user_id):
    """
    Delete a specific user by ID. Only the account owner or an admin can delete an account.
    
    URL Parameters:
        user_id: The ID of the user to delete
        
    Returns:
        JSON response with a success message.
    """
    try:
        # Query the user by ID
        user = User.query.get(user_id)
        
        # If user does not exist
        if not user:
            return utils.error_response('User not found', 404)
        
        # Delete the user from the database
        # All related entries will be cascade-deleted due to relationship setup
        db.session.delete(user)
        db.session.commit()
        
        return utils.success_response('User deleted successfully')
        
    except Exception as e:
        db.session.rollback()
        return utils.error_response(f'Error deleting user: {str(e)}', 500)