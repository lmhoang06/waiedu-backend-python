from sqlalchemy import func, CheckConstraint
from sqlalchemy.orm import relationship

from ..services.postgresql import db

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    price = db.Column(db.BigInteger, nullable=False, default=0)
    currency_code = db.Column(db.String(3), nullable=False, default='VND')
    subject_id = db.Column(db.String(50), db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.TIMESTAMP(timezone=False), server_default=func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP(timezone=False), server_default=func.current_timestamp())
    
    # Table constraints - in SQLAlchemy we can define them as part of __table_args__
    __table_args__ = (
        # Note: The check_user_role function constraint isn't directly expressible in SQLAlchemy ORM
        # It will be created by the SQL directly but won't be represented here
        CheckConstraint('price >= 0', name='check_course_price_positive'),
        CheckConstraint("currency_code = 'VND'", name='check_course_currency_code'),
    )
    
    # Relationships - changed from backref to back_populates
    teacher = relationship(
        "User", 
        foreign_keys=[teacher_user_id], 
        back_populates="taught_courses"
    )
    
    subject = relationship(
        "Subject", 
        foreign_keys=[subject_id], 
        back_populates="courses"
    )
    
    # Relationship to student enrollments
    enrollments = relationship(
        "StudentEnrollment",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Relationship to Class (One-to-Many)
    classes = relationship(
        "Class",
        back_populates="course", # Links to the 'course' attribute in the Class model
        cascade="all, delete-orphan", # Ensures classes are deleted if the course is deleted (matches ON DELETE CASCADE)
        lazy="dynamic", # Good practice for potentially large collections
        order_by="Class.scheduled_start_time" # Optional: Default ordering when accessing course.classes
    )

    def __repr__(self):
        return f'<Course id={self.id} title={self.title}>'