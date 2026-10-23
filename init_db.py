from flask import Flask
from database import db, User, Document, DocumentPermission, AuditLog

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trustvault.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    print("Users table:", User.__tablename__)
    print("Documents table:", Document.__tablename__)
    print("Permissions table:", DocumentPermission.__tablename__)
    print("Audit logs table:", AuditLog.__tablename__)

    print("\nTrustVault database verification completed!")