from sqlalchemy import func, CheckConstraint, ForeignKey, String, Text, Boolean, TIMESTAMP, Integer, BigInteger
from sqlalchemy.orm import relationship
from ..services.postgresql import db # Assuming this is your Flask-SQLAlchemy or similar db instance

class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True) # Added index=True based on SQL idx_classes_course_id
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_published = db.Column(db.Boolean, default=False, nullable=False) # Explicitly nullable=False is good practice with defaults
    scheduled_start_time = db.Column(db.TIMESTAMP(timezone=False), nullable=False, index=True) # Added index=True based on SQL idx_classes_scheduled_start_time
    scheduled_end_time = db.Column(db.TIMESTAMP(timezone=False), nullable=False)

    # Timestamps managed by the database trigger/defaults, mirroring the SQL setup
    created_at = db.Column(db.TIMESTAMP(timezone=False), server_default=func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP(timezone=False), server_default=func.current_timestamp()) # Relying on DB trigger for updates

    # Define the table-level CHECK constraint
    __table_args__ = (
        CheckConstraint('scheduled_end_time > scheduled_start_time', name='check_class_schedule_times'),
        # Note: The SQL trigger for updated_at is defined in the DB, not here.
        # Note: The SQL index idx_classes_course_id is implicitly created by index=True on course_id
        # Note: The SQL index idx_classes_scheduled_start_time is implicitly created by index=True on scheduled_start_time
    )

    # Relationship to Course (Many-to-One)
    course = relationship(
        "Course",
        back_populates="classes" # Links to the 'classes' attribute in the Course model
    )

    def __repr__(self):
        return f'<Class id={self.id} title={self.title} course_id={self.course_id}>'