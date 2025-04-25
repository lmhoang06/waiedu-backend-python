from sqlalchemy import UniqueConstraint

from ..services.postgresql import db

class UserSubject(db.Model):
    __tablename__ = 'user_subjects'

    __table_args__ = (
        UniqueConstraint('user_id', 'subject_id', name='user_subject_unique'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.String(50), db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)

    # Relationships back to User and Subject models
    # Use strings "User" and "Subject" to avoid circular imports
    user = db.relationship("User", back_populates="user_subjects")
    subject = db.relationship("Subject", back_populates="user_subjects")

    def __repr__(self):
        return f'<UserSubject user_id={self.user_id} subject_id={self.subject_id}>'