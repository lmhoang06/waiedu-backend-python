from sqlalchemy import (
    Enum as SQLAlchemyEnum, func
)
from sqlalchemy.orm import relationship

from ..services.postgresql import db
from .enums import UserGender, UserRole

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Remember to hash passwords!
    phone = db.Column(db.String(20), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)

    gender = db.Column(
        SQLAlchemyEnum(UserGender, name='user_gender', create_type=False),
        nullable=True
    )
    role = db.Column(
        SQLAlchemyEnum(UserRole, name='user_role', create_type=False),
        nullable=False,
        default=UserRole.student
    )

    grade = db.Column(db.String(20), nullable=True)
    school = db.Column(db.String(255), nullable=True)
    teaching_subject = db.Column(db.String(255), nullable=True)
    child_grade = db.Column(db.String(20), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(255), nullable=True)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.TIMESTAMP(timezone=False), nullable=True)

    created_at = db.Column(db.TIMESTAMP(timezone=False), server_default=func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP(timezone=False), server_default=func.current_timestamp()) # Trigger handles updates

    # Relationship to the UserSubject association model
    # Use string "UserSubject" to avoid circular import
    user_subjects = db.relationship(
        "UserSubject",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True
    )
    
    # Relationships for parent-child links
    # Modified to use back_populates to match ParentChildLink model
    
    # For parent users - get links to their children
    children_links = relationship(
        "ParentChildLink",
        foreign_keys="ParentChildLink.parent_user_id",
        back_populates="parent",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    # For child users - get links to their parents
    parent_links = relationship(
        "ParentChildLink",
        foreign_keys="ParentChildLink.child_user_id",
        back_populates="child",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    # Relationship to course enrollments (for student users)
    # Changed from backref to back_populates to match StudentEnrollment model
    course_enrollments = relationship(
        "StudentEnrollment",
        foreign_keys="StudentEnrollment.student_user_id",
        back_populates="student",
        lazy="dynamic"
    )
    
    # Relationship to taught courses (for teacher users)
    taught_courses = relationship(
        "Course",
        foreign_keys="Course.teacher_user_id",
        back_populates="teacher",
        lazy="dynamic"
    )

    def __repr__(self):
        return f'<User id={self.id} email={self.email} role={self.role.value}>'