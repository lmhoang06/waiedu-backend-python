from sqlalchemy import PrimaryKeyConstraint

from ..services.postgresql import db

class ParentChildLink(db.Model):
    __tablename__ = 'parent_child_links'

    # Define composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('parent_user_id', 'child_user_id'),
    )

    # No id column as we're using a composite primary key
    parent_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    child_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Relationships back to User model - using back_populates instead of backref
    # Use strings "User" to avoid circular imports
    # We need different relationship names for parent and child
    parent = db.relationship("User", foreign_keys=[parent_user_id], back_populates="children_links")
    child = db.relationship("User", foreign_keys=[child_user_id], back_populates="parent_links")

    def __repr__(self):
        return f'<ParentChildLink parent_id={self.parent_user_id} child_id={self.child_user_id}>'