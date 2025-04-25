from ..services.postgresql import db

class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Relationship to the UserSubject association model
    # Use string "UserSubject" to avoid circular import
    user_subjects = db.relationship(
        "UserSubject",
        back_populates="subject",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f'<Subject id={self.id} name={self.name}>'