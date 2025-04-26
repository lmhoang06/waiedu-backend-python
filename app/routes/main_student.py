from flask import Blueprint, jsonify, request
from app.models import StudentEnrollment, Course, User
from app.services.postgresql import db
from app.services.jwt_service import decode_jwt
from app import utils
import os

# Create a blueprint for student routes
main_student_bp = Blueprint('main_student', __name__, url_prefix='/main/student')

def authenticate_request():
    """
    Authenticate the request using the JWT token in the Authorization header.

    Returns:
        User object if authentication is successful, or a JSON error response if failed.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return utils.error_response('Authorization token is missing or invalid', 401)

    token = auth_header.split(' ')[1]
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'default_secret_key')

    try:
        payload = decode_jwt(token, jwt_secret)
        user_id = payload.get('userId')
        if not user_id:
            return utils.error_response('Invalid token payload', 401)

        user = User.query.get(user_id)
        if not user:
            return utils.error_response('User not found', 404)

        return user
    except Exception as e:
        return utils.error_response(f'Authentication failed: {str(e)}', 401)

@main_student_bp.route('/enrollments', methods=['GET'])
def get_enrollments():
    """
    Retrieve all enrollments for the authenticated student.

    Returns:
        JSON response with a list of enrollments.
    """
    auth_result = authenticate_request()
    if isinstance(auth_result, tuple):
        return auth_result

    student_user = auth_result

    try:
        # Query enrollments for the student
        enrollments = StudentEnrollment.query.filter_by(student_user_id=student_user.id).all()

        # Serialize enrollments
        enrollment_data = [
            {
                'course_id': enrollment.course_id,
                'course_title': enrollment.course.title if enrollment.course else None,
                'progress': enrollment.progress,
                'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None
            }
            for enrollment in enrollments
        ]

        return utils.success_response('Enrollments retrieved successfully', {'enrollments': enrollment_data})

    except Exception as e:
        return utils.error_response(f'Error retrieving enrollments: {str(e)}', 500)

@main_student_bp.route('/courses', methods=['GET'])
def get_available_courses():
    """
    Retrieve all available courses for students.

    Returns:
        JSON response with a list of courses.
    """
    auth_result = authenticate_request()
    if isinstance(auth_result, tuple):
        return auth_result

    try:
        # Query all published courses
        courses = Course.query.filter_by(is_published=True).all()

        # Serialize courses
        course_data = [
            {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'price': course.price,
                'currency_code': course.currency_code
            }
            for course in courses
        ]

        return utils.success_response('Courses retrieved successfully', {'courses': course_data})

    except Exception as e:
        return utils.error_response(f'Error retrieving courses: {str(e)}', 500)

@main_student_bp.route('/enroll', methods=['POST'])
def enroll_in_course():
    """
    Enroll the authenticated student in a course.

    Expected request body:
    {
        "course_id": 2
    }

    Returns:
        JSON response with enrollment details.
    """
    auth_result = authenticate_request()
    if isinstance(auth_result, tuple):
        return auth_result

    student_user = auth_result

    data, error = utils.get_request_data()
    if error:
        return error

    course_id = data.get('course_id')

    if not course_id:
        return utils.error_response('Course ID is required', 400)

    try:
        # Check if the course exists and is published
        course = Course.query.filter_by(id=course_id, is_published=True).first()
        if not course:
            return utils.error_response('Course not found or not available', 404)

        # Check if the student is already enrolled
        existing_enrollment = StudentEnrollment.query.filter_by(student_user_id=student_user.id, course_id=course_id).first()
        if existing_enrollment:
            return utils.error_response('Student is already enrolled in this course', 409)

        # Create a new enrollment
        new_enrollment = StudentEnrollment(
            student_user_id=student_user.id,
            course_id=course_id,
            price_at_enrollment=course.price,
            currency_at_enrollment=course.currency_code
        )

        db.session.add(new_enrollment)
        db.session.commit()

        return utils.success_response('Enrollment successful', {
            'enrollment': {
                'course_id': new_enrollment.course_id,
                'course_title': course.title,
                'enrollment_date': new_enrollment.enrollment_date.isoformat()
            }
        }, 201)

    except Exception as e:
        db.session.rollback()
        return utils.error_response(f'Error during enrollment: {str(e)}', 500)