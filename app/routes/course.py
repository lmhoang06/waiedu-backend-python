from flask import Blueprint, jsonify, request
from app.models import Course, Subject, User, StudentEnrollment
from app.services.postgresql import db, ensure_db_connection
from app import utils
from app.models.enums import UserRole
from functools import wraps

# Create a blueprint for course routes
main_courses_bp = Blueprint('main_courses', __name__, url_prefix='/main/courses')

def role_required(*roles):
    """
    Decorator to check if the authenticated user has one of the required roles
    
    Args:
        roles: List of roles that are allowed to access the route
        
    Returns:
        Decorated function that checks user role before execution
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Authenticate the request
            auth_result = utils.authenticate_request()
            if isinstance(auth_result, tuple):
                return auth_result
                
            # Check if user has one of the required roles
            user = auth_result
            if user.role.value not in roles:
                return utils.error_response('Permission denied. Insufficient role privileges.', 403)
                
            return f(user, *args, **kwargs)
        return decorated_function
    return decorator

@main_courses_bp.route('', methods=['GET'])
@ensure_db_connection
def get_courses():
    """
    Retrieve all published courses (for all authenticated users)
    
    Query Parameters:
        $select: Comma-separated list of fields to include in the response
        $subject: Comma-separated list of subject IDs to filter courses by
        $teacher: Comma-separated list of teacher IDs to filter courses by
        
    Returns:
        JSON response with a list of courses.
    """
    # Authenticate the request
    auth_result = utils.authenticate_request()
    if isinstance(auth_result, tuple):
        return auth_result
        
    # Get query parameters
    select_fields = request.args.get('$select', '')
    subject_ids = request.args.get('$subject', '')
    teacher_ids = request.args.get('$teacher', '')
    
    try:
        # Start with base query for published courses
        query = Course.query.filter_by(is_published=True)
        
        # Add subject filter if provided
        if subject_ids:
            # Split comma-separated values and filter
            subject_id_list = [s.strip() for s in subject_ids.split(',') if s.strip()]
            if subject_id_list:
                # Apply OR condition for multiple subjects
                query = query.filter(Course.subject_id.in_(subject_id_list))
        
        # Add teacher filter if provided
        if teacher_ids:
            # Split comma-separated values and convert to integers
            try:
                teacher_id_list = [int(t.strip()) for t in teacher_ids.split(',') if t.strip()]
                if teacher_id_list:
                    # Apply OR condition for multiple teachers
                    query = query.filter(Course.teacher_user_id.in_(teacher_id_list))
            except ValueError:
                # Handle case where teacher IDs are not valid integers
                return utils.error_response('Invalid teacher ID format. Teacher IDs must be integers.', 400)
        
        # Execute the query
        courses = query.all()
        
        # Prepare response data
        courses_data = []
        
        for course in courses:
            # Basic fields available to all roles
            all_fields = {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'category': course.category,
                'image_url': course.image_url,
                'price': course.price,
                'currency_code': course.currency_code,
                'subject_id': course.subject_id,
                'teacher_user_id': course.teacher_user_id,
            }
            
            # If $select is specified, filter the fields
            if select_fields:
                requested_fields = [field.strip() for field in select_fields.split(',')]
                filtered_data = {field: all_fields[field] for field in requested_fields if field in all_fields}
                
                # Make sure we always include at least the ID
                if 'id' not in filtered_data:
                    filtered_data['id'] = all_fields['id']
                
                course_data = filtered_data
            else:
                # If no selection, return all fields
                course_data = all_fields
                
            # Include teacher name if available
            if course.teacher:
                course_data['teacher_name'] = course.teacher.name
                
            # Include subject name if available
            if course.subject:
                course_data['subject_name'] = course.subject.name
                
            courses_data.append(course_data)
        
        # Include subject and teacher metadata if filters were applied
        response_data = {'courses': courses_data}
        
        # If filtering by a single subject, include subject info
        if subject_ids and len(subject_ids.split(',')) == 1 and not ',' in subject_ids:
            subject = Subject.query.get(subject_ids)
            if subject:
                response_data['subject'] = {
                    'id': subject.id,
                    'name': subject.name
                }
                
        # If filtering by a single teacher, include teacher info
        if teacher_ids and len(teacher_ids.split(',')) == 1 and not ',' in teacher_ids:
            try:
                teacher_id = int(teacher_ids)
                teacher = User.query.get(teacher_id)
                if teacher and teacher.role == UserRole.teacher:
                    response_data['teacher'] = {
                        'id': teacher.id,
                        'name': teacher.name
                    }
            except ValueError:
                # Skip adding teacher info if ID is not valid
                pass
        
        return utils.success_response('Courses retrieved successfully', response_data)
        
    except Exception as e:
        return utils.error_response(f'Error retrieving courses: {str(e)}', 500)

@main_courses_bp.route('/<int:course_id>', methods=['GET'])
@ensure_db_connection
def get_course(course_id):
    """
    Retrieve information about a specific course by its ID.
    
    URL Parameters:
        course_id: The ID of the course
        
    Query Parameters:
        $select: Comma-separated list of fields to include in the response
        
    Returns:
        JSON response with the course details
    """
    # Authenticate the request
    auth_result = utils.authenticate_request()
    if isinstance(auth_result, tuple):
        return auth_result
    
    # Get the $select query parameter
    select_fields = request.args.get('$select', '')
    
    try:
        # Query the course by ID 
        course = Course.query.get(course_id)
        
        # If course does not exist
        if not course:
            return utils.error_response('Course not found', 404)
        
        # Only allow access to published courses unless you're the teacher of this course or an admin
        user = auth_result
        if not course.is_published and (user.role != UserRole.teacher or course.teacher_user_id != user.id):
            return utils.error_response('Course not found or not available', 404)
        
        # All available fields
        all_fields = {
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'price': course.price,
            'currency_code': course.currency_code,
            'teacher_user_id': course.teacher_user_id,
            'category': course.category,
            'image_url': course.image_url, 
            'subject_id': course.subject_id,
            'is_published': course.is_published,
            'created_at': course.created_at.isoformat() if course.created_at else None,
            'updated_at': course.updated_at.isoformat() if course.updated_at else None
        }
        
        # If $select is specified, filter the fields
        if select_fields:
            requested_fields = [field.strip() for field in select_fields.split(',')]
            filtered_data = {field: all_fields[field] for field in requested_fields if field in all_fields}
            
            # Make sure we always include at least the ID
            if 'id' not in filtered_data:
                filtered_data['id'] = all_fields['id']
            
            course_data = filtered_data
        else:
            # If no selection, return all fields
            course_data = all_fields
        
        # Include teacher name if available
        if course.teacher:
            course_data['teacher_name'] = course.teacher.name
            
        # Include subject name if available
        if course.subject:
            course_data['subject_name'] = course.subject.name
            
        # Include enrollment count
        enrollment_count = StudentEnrollment.query.filter_by(course_id=course_id).count()
        course_data['enrollment_count'] = enrollment_count
        
        return utils.success_response('Course retrieved successfully', {'course': course_data})
    
    except Exception as e:
        return utils.error_response(f'Error retrieving course: {str(e)}', 500)

@main_courses_bp.route('', methods=['POST'])
@ensure_db_connection
@role_required('teacher')
def create_course(user):
    """
    Create a new course (teacher only)
    
    Expected request body:
    {
        "title": "Course Title",
        "description": "Course description",
        "price": 100000,
        "subject_id": "math",
        "category": "High School",
        "image_url": "https://example.com/image.jpg"
    }
    
    Returns:
        JSON response with the created course data
    """
    # Get JSON data from request
    course_data, error = utils.get_request_data()
    if error:
        return error
    
    # Extract and validate required fields
    title = course_data.get('title')
    if not title:
        return utils.error_response('Title is required', 400)
    
    # Extract optional fields with defaults
    description = course_data.get('description', '')
    price = course_data.get('price', 0)
    currency_code = course_data.get('currency_code', 'VND')
    subject_id = course_data.get('subject_id')
    category = course_data.get('category')
    image_url = course_data.get('image_url')
    is_published = course_data.get('is_published', False)
    
    # Validate price is non-negative
    if price < 0:
        return utils.error_response('Price cannot be negative', 400)
    
    # Validate subject_id if provided
    if subject_id:
        subject = Subject.query.get(subject_id)
        if not subject:
            return utils.error_response(f'Subject with ID {subject_id} not found', 400)
    
    try:
        # Create new course
        new_course = Course(
            title=title,
            description=description,
            price=price,
            currency_code=currency_code,
            teacher_user_id=user.id,
            subject_id=subject_id,
            category=category,
            image_url=image_url,
            is_published=is_published
        )
        
        # Add to database
        db.session.add(new_course)
        db.session.commit()
        
        # Prepare response data
        course_data = {
            'id': new_course.id,
            'title': new_course.title,
            'description': new_course.description,
            'price': new_course.price,
            'currency_code': new_course.currency_code,
            'teacher_user_id': new_course.teacher_user_id,
            'subject_id': new_course.subject_id,
            'category': new_course.category,
            'image_url': new_course.image_url,
            'is_published': new_course.is_published,
            'created_at': new_course.created_at.isoformat() if new_course.created_at else None
        }
        
        return utils.success_response('Course created successfully', {'course': course_data}, 201)
        
    except Exception as e:
        db.session.rollback()
        return utils.error_response(f'Error creating course: {str(e)}', 500)

@main_courses_bp.route('/<int:course_id>', methods=['PUT', 'PATCH'])
@ensure_db_connection
@role_required('teacher')
def update_course(user, course_id):
    """
    Update an existing course (teacher only, and only their own courses)
    
    URL Parameters:
        course_id: The ID of the course to update
        
    Expected request body:
    {
        "title": "Updated Course Title",
        "description": "Updated course description",
        ... (other fields to update)
    }
    
    Returns:
        JSON response with the updated course data
    """
    # Get JSON data from request
    update_data, error = utils.get_request_data()
    if error:
        return error
    
    try:
        # Query the course by ID
        course = Course.query.get(course_id)
        
        # If course does not exist
        if not course:
            return utils.error_response('Course not found', 404)
        
        # Check if user is the owner of the course
        if course.teacher_user_id != user.id:
            return utils.error_response('Permission denied. You can only update your own courses', 403)
        
        # Update fields if they exist in the request
        if 'title' in update_data:
            course.title = update_data['title']
            
        if 'description' in update_data:
            course.description = update_data['description']
            
        if 'price' in update_data:
            price = update_data['price']
            if price < 0:
                return utils.error_response('Price cannot be negative', 400)
            course.price = price
            
        if 'currency_code' in update_data:
            if update_data['currency_code'] != 'VND':
                return utils.error_response('Only VND currency is supported', 400)
            course.currency_code = update_data['currency_code']
            
        if 'subject_id' in update_data:
            subject_id = update_data['subject_id']
            if subject_id:
                subject = Subject.query.get(subject_id)
                if not subject:
                    return utils.error_response(f'Subject with ID {subject_id} not found', 400)
            course.subject_id = subject_id
            
        if 'category' in update_data:
            course.category = update_data['category']
            
        if 'image_url' in update_data:
            course.image_url = update_data['image_url']
            
        if 'is_published' in update_data:
            course.is_published = update_data['is_published']
        
        # Save changes to database
        db.session.commit()
        
        # Prepare response data
        course_data = {
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'price': course.price,
            'currency_code': course.currency_code,
            'teacher_user_id': course.teacher_user_id,
            'subject_id': course.subject_id,
            'category': course.category,
            'image_url': course.image_url,
            'is_published': course.is_published,
            'updated_at': course.updated_at.isoformat() if course.updated_at else None
        }
        
        return utils.success_response('Course updated successfully', {'course': course_data})
        
    except Exception as e:
        db.session.rollback()
        return utils.error_response(f'Error updating course: {str(e)}', 500)

@main_courses_bp.route('/<int:course_id>', methods=['DELETE'])
@ensure_db_connection
@role_required('teacher')
def delete_course(user, course_id):
    """
    Delete a course (teacher only, and only their own courses)
    
    URL Parameters:
        course_id: The ID of the course to delete
        
    Returns:
        JSON response with success message
    """
    try:
        # Query the course by ID
        course = Course.query.get(course_id)
        
        # If course does not exist
        if not course:
            return utils.error_response('Course not found', 404)
        
        # Check if user is the owner of the course
        if course.teacher_user_id != user.id:
            return utils.error_response('Permission denied. You can only delete your own courses', 403)
        
        # Delete the course (will cascade delete enrollments due to relationship setup)
        db.session.delete(course)
        db.session.commit()
        
        return utils.success_response('Course deleted successfully')
        
    except Exception as e:
        db.session.rollback()
        return utils.error_response(f'Error deleting course: {str(e)}', 500)

@main_courses_bp.route('/my', methods=['GET'])
@ensure_db_connection
@role_required('teacher')
def get_my_courses(user):
    """
    Get all courses created by the authenticated teacher.
    
    Returns:
        JSON response with list of courses
    """
    try:
        # Query all courses by the current teacher
        courses = Course.query.filter_by(teacher_user_id=user.id).all()
            
        # Prepare response data
        courses_data = []
        for course in courses:
            course_data = {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'price': course.price,
                'currency_code': course.currency_code,
                'category': course.category,
                'image_url': course.image_url,
                'subject_id': course.subject_id,
                'is_published': course.is_published,
                'created_at': course.created_at.isoformat() if course.created_at else None,
                'updated_at': course.updated_at.isoformat() if course.updated_at else None
            }
            
            # Include subject name if available
            if course.subject:
                course_data['subject_name'] = course.subject.name
                
            # Include enrollment count
            enrollment_count = StudentEnrollment.query.filter_by(course_id=course.id).count()
            course_data['enrollment_count'] = enrollment_count
                
            courses_data.append(course_data)
            
        return utils.success_response('My courses retrieved successfully', {'courses': courses_data})
        
    except Exception as e:
        return utils.error_response(f'Error retrieving your courses: {str(e)}', 500)

@main_courses_bp.route('/<int:course_id>/analytics', methods=['GET'])
@ensure_db_connection
@role_required('teacher', 'admin')
def get_course_analytics(user, course_id):
    """
    Get analytics data for a specific course.
    Accessible by:
    - Admin: Can access analytics for any course
    - Teacher: Can only access analytics for courses they created
    
    URL Parameters:
        course_id: The ID of the course
        
    Returns:
        JSON response with course analytics data
    """
    try:
        # Query the course by ID
        course = Course.query.get(course_id)
        
        # If course does not exist
        if not course:
            return utils.error_response('Course not found', 404)
        
        # Check permissions:
        # - Admins can access analytics for any course
        # - Teachers can only access analytics for their own courses
        if user.role == UserRole.teacher and course.teacher_user_id != user.id:
            return utils.error_response('Permission denied. You can only view analytics for your own courses.', 403)
        
        # Get enrollment count
        enrollment_count = StudentEnrollment.query.filter_by(course_id=course_id).count()
        
        # Calculate total revenue (price at enrollment * number of enrollments)
        # We use the price recorded at enrollment time for accurate historical data
        enrollments = StudentEnrollment.query.filter_by(course_id=course_id).all()
        total_revenue = sum(enrollment.price_at_enrollment for enrollment in enrollments)
        
        # Prepare analytics data
        analytics_data = {
            'course_id': course_id,
            'course_title': course.title,
            'enrollment_count': enrollment_count,
            'total_revenue': total_revenue,
            'currency_code': course.currency_code
        }
        
        return utils.success_response('Course analytics retrieved successfully', {'analytics': analytics_data})
        
    except Exception as e:
        return utils.error_response(f'Error retrieving course analytics: {str(e)}', 500)

@main_courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@ensure_db_connection
@role_required('student')
def enroll_in_course(course_id):
    """
    Enroll the authenticated student in a course.
    
    URL Parameters:
        course_id: The ID of the course to enroll in
        
    Returns:
        JSON response with enrollment details.
    """
    # Authenticate the request
    auth_result = utils.authenticate_request()
    if isinstance(auth_result, tuple):
        return auth_result
        
    user = auth_result
    
    # Check if user is a student
    if user.role != UserRole.student:
        return utils.error_response('Only students can enroll in courses', 403)

    try:
        # Check if the course exists and is published
        course = Course.query.filter_by(id=course_id, is_published=True).first()
        if not course:
            return utils.error_response('Course not found or not available', 404)

        # Check if the student is already enrolled
        existing_enrollment = StudentEnrollment.query.filter_by(student_user_id=user.id, course_id=course_id).first()
        if existing_enrollment:
            return utils.error_response('You are already enrolled in this course', 409)

        # Create a new enrollment
        new_enrollment = StudentEnrollment(
            student_user_id=user.id,
            course_id=course_id,
            price_at_enrollment=course.price,
            currency_at_enrollment=course.currency_code
        )

        db.session.add(new_enrollment)
        db.session.commit()

        return utils.success_response('Successfully enrolled in the course', {
            'enrollment': {
                'course_id': new_enrollment.course_id,
                'course_title': course.title,
                'enrollment_date': new_enrollment.enrollment_date.isoformat() if new_enrollment.enrollment_date else None
            }
        }, 201)

    except Exception as e:
        db.session.rollback()
        return utils.error_response(f'Error during enrollment: {str(e)}', 500)