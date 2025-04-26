from flask import Blueprint, jsonify, request, redirect, url_for
from app.models import StudentEnrollment, Course, User
from app.services.postgresql import db, ensure_db_connection
from app.services.jwt_service import decode_jwt
from app import utils

# Create a blueprint for student routes
main_student_bp = Blueprint('main_student', __name__, url_prefix='/main/student')

@main_student_bp.route('/enrollments', methods=['GET'])
@ensure_db_connection
def get_enrollments():
    """
    Retrieve all enrollments for the authenticated student.

    Returns:
        JSON response with a list of enrollments.
    """
    auth_result = utils.authenticate_request()
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
