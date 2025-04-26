from sqlalchemy import func, CheckConstraint, UniqueConstraint

from ..services.postgresql import db

class StudentEnrollment(db.Model):
    __tablename__ = 'student_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    
    enrollment_date = db.Column(db.TIMESTAMP(timezone=False), server_default=func.current_timestamp(), nullable=False)
    last_accessed = db.Column(db.TIMESTAMP(timezone=False), nullable=True)
    progress = db.Column(db.SmallInteger, default=0, nullable=False)
    completed_date = db.Column(db.TIMESTAMP(timezone=False), nullable=True)
    
    # Price and currency capture at enrollment time
    price_at_enrollment = db.Column(db.BigInteger, nullable=False, default=0)
    currency_at_enrollment = db.Column(db.String(3), nullable=False, default='VND')
    
    # Table constraints defined in __table_args__
    __table_args__ = (
        # Note: The check_user_role function constraint isn't directly expressible in SQLAlchemy ORM
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
        CheckConstraint('price_at_enrollment >= 0', name='check_enrollment_price_positive'),
        CheckConstraint("currency_at_enrollment = 'VND'", name='check_enrollment_currency_code'),
        UniqueConstraint('student_user_id', 'course_id', name='unique_student_course_enrollment')
    )
    
    # Relationships - using back_populates on both sides instead of backref
    student = db.relationship("User", foreign_keys=[student_user_id], back_populates="course_enrollments")
    course = db.relationship("Course", foreign_keys=[course_id], back_populates="enrollments")
    
    def __repr__(self):
        return f'<StudentEnrollment id={self.id} student_id={self.student_user_id} course_id={self.course_id}>'