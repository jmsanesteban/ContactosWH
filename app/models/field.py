from datetime import datetime
from ..extensions import db


class FieldDefinition(db.Model):
    __tablename__ = 'field_definitions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    display_name = db.Column(db.String(128), nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    field_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    values = db.relationship('ContactValue', backref='field', lazy='dynamic',
                             cascade='all, delete-orphan')

    def __repr__(self):
        return f'<FieldDefinition {self.name}>'
