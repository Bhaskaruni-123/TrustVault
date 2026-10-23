
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), unique=True, nullable=False)
    owner_email = db.Column(
        db.String(120),
        db.ForeignKey("user.email"),
        nullable=False
    )
    uploaded_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )


class DocumentPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("document.id"),
        nullable=False
    )
    viewer_email = db.Column(db.String(120), nullable=False)
    can_view = db.Column(db.Boolean, default=True, nullable=False)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    document_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )
