import os

from flask import Flask, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

from database import db, User, Document, DocumentPermission, AuditLog

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-key-change-before-deployment"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trustvault.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "png", "jpg", "jpeg"}

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "private_documents"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)


def create_demo_users():
    demo_users = [
        ("admin@trustvault.com", "Admin@123", "Admin"),
        ("owner@trustvault.com", "Owner@123", "Owner"),
        ("viewer@trustvault.com", "Viewer@123", "Viewer"),
    ]

    for email, password, role in demo_users:
        existing_user = User.query.filter_by(email=email).first()

        if not existing_user:
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                role=role
            )
            db.session.add(user)

    db.session.commit()


with app.app_context():
    db.create_all()
    create_demo_users()


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TrustVault</title>
        <style>
            body {
                font-family: Arial;
                background: #f1f5f9;
                text-align: center;
                margin: 0;
            }
            header {
                background: #0f172a;
                color: white;
                padding: 25px;
                font-size: 28px;
            }
            .box {
                background: white;
                max-width: 650px;
                margin: 100px auto;
                padding: 40px;
                border-radius: 12px;
            }
            a {
                display: inline-block;
                background: #2563eb;
                color: white;
                padding: 14px 28px;
                border-radius: 6px;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <header>TrustVault 🔐</header>
        <div class="box">
            <h1>Secure Document Sharing</h1>
            <p>Protect confidential documents with controlled access.</p>
            <p>Your documents. Your permissions. Your security.</p>
            <a href="/login">Get Started</a>
        </div>
    </body>
    </html>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["email"] = user.email
            session["role"] = user.role

            db.session.add(
                AuditLog(
                    user_email=user.email,
                    action="LOGIN"
                )
            )
            db.session.commit()

            return redirect(url_for("dashboard"))

        message = "Invalid email or password. Please try again."

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TrustVault Login</title>
        <style>
            body {{
                font-family: Arial;
                background: #f1f5f9;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .box {{
                background: white;
                padding: 35px;
                width: 320px;
                border-radius: 12px;
            }}
            input, button {{
                width: 100%;
                box-sizing: border-box;
                padding: 12px;
                margin: 10px 0;
            }}
            button {{
                background: #2563eb;
                color: white;
                border: none;
                cursor: pointer;
            }}
            .error {{ color: #dc2626; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>TrustVault Login</h2>
            <p class="error">{message}</p>
            <form method="POST" action="/login">
                <input type="email" name="email"
                       placeholder="Email address" required>
                <input type="password" name="password"
                       placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <a href="/">Back to Home</a>
        </div>
    </body>
    </html>
    """


@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))

    role = session["role"]
    email = session["email"]

    if role == "Admin":
        content = """
            <h3>Admin Dashboard</h3>
            <p>Manage users and monitor activity.</p>
            <a href="/admin-audit">View Audit Logs</a>
        """
    elif role == "Owner":
        content = """
            <h3>Owner Dashboard</h3>
            <p>Upload documents and manage permissions.</p>
            <a href="/upload">Upload Document</a>
            <br><br>
            <a href="/my-documents">My Documents</a>
        """
    else:
        content = """
            <h3>Viewer Dashboard</h3>
            <p>Access documents shared with you.</p>
            <a href="/shared-documents">My Shared Documents</a>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TrustVault Dashboard</title>
    </head>
    <body style="font-family:Arial;background:#f1f5f9;text-align:center;padding:60px">
        <div style="background:white;padding:35px;border-radius:12px;max-width:600px;margin:auto">
            <h1>TrustVault 🔐</h1>
            <p>Welcome, {role}!</p>
            <p>Logged in as: {email}</p>
            {content}
            <a href="/logout">Logout</a>
        </div>
    </body>
    </html>
    """


@app.route("/logout")
def logout():
    if "email" in session:
        db.session.add(
            AuditLog(
                user_email=session["email"],
                action="LOGOUT"
            )
        )
        db.session.commit()

    session.clear()
    return redirect(url_for("home"))

@app.route("/upload", methods=["GET", "POST"])
def upload_document():
    if "email" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Owner":
        return "Access denied: Only document owners can upload files.", 403

    message = ""

    if request.method == "POST":
        file = request.files.get("document")

        if not file or not file.filename:
            message = "Please select a file."
        else:
            original_name = secure_filename(file.filename)

            if not original_name:
                message = "Invalid filename."
            elif "." not in original_name or original_name.rsplit(".", 1)[1].lower() not in ALLOWED_EXTENSIONS:
                message = "File type not allowed. Upload PDF, TXT, DOCX, PNG, JPG, or JPEG files only."
            else:
                stored_name = str(uuid.uuid4()) + "_" + original_name
                file_path = os.path.join(UPLOAD_FOLDER, stored_name)

                try:
                    file.save(file_path)

                    document = Document(
                        original_name=original_name,
                        stored_name=stored_name,
                        owner_email=session["email"]
                    )

                    db.session.add(document)
                    db.session.flush()

                    db.session.add(
                        AuditLog(
                            user_email=session["email"],
                            action="DOCUMENT_UPLOAD",
                            document_id=document.id
                        )
                    )

                    db.session.commit()
                    message = "Document uploaded successfully!"

                except Exception:
                    db.session.rollback()

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    app.logger.exception("Document upload failed")
                    message = "Upload failed. Please try again."

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload Document - TrustVault</title>
    </head>
    <body style="font-family:Arial;background:#f1f5f9;text-align:center;padding:50px">
        <div style="background:white;padding:30px;border-radius:12px;max-width:500px;margin:auto">
            <h1>Secure Document Upload</h1>
            <p>{message}</p>

            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="document" required>
                <br><br>
                <button type="submit">Upload Document</button>
            </form>

            <br>
            <a href="/dashboard">Back to Dashboard</a>
        </div>
    </body>
    </html>
    """
@app.route("/my-documents")
def my_documents():
    if "email" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Owner":
        return "Access denied: Only document owners can view this page.", 403

    documents = Document.query.filter_by(
        owner_email=session["email"]
    ).all()

    document_list = ""

    for document in documents:
        document_list += f"""
        <li>
            <strong>{document.original_name}</strong>
            - Uploaded at: {document.uploaded_at}
            <br>
            <a href="/view-document/{document.id}">View Document</a>
            |
            <a href="/share-document/{document.id}">Share Document</a>
        </li>
        <br>
    """
    

    if not document_list:
        document_list = "<p>No documents uploaded yet.</p>"

    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>My Documents - TrustVault</title>
        </head>
        <body style="font-family:Arial;background:#f1f5f9;padding:40px">
            <div style="background:white;padding:30px;border-radius:12px;max-width:700px;margin:auto">
                <h1>My Documents</h1>
                <p>Your uploaded documents are listed below.</p>
                <ul>{document_list}</ul>
                <a href="/upload">Upload Another Document</a>
                <br><br>
                <a href="/dashboard">Back to Dashboard</a>
            </div>
        </body>
        </html>
    """
@app.route("/view-document/<int:document_id>")
def view_document(document_id):
    # Check login
    if "email" not in session:
        return redirect(url_for("login"))

    # Find the document
    document = db.session.get(Document, document_id)

    if document is None:
        return "Document not found.", 404

    # Check whether the logged-in user is the owner
    is_owner = (
        session.get("role") == "Owner"
        and document.owner_email == session["email"]
    )
    # Check whether the logged-in viewer has explicit permission
    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        viewer_email=session["email"],
        can_view=True
    ).first()
    is_authorized_viewer = (
        session.get("role") == "Viewer"
        and permission is not None
    )
    if not (is_owner or is_authorized_viewer):
        return "Access denied.", 403

    # Build the private file path
    file_path = os.path.join(
        UPLOAD_FOLDER,
        document.stored_name
    )

    # Check that the file exists
    if not os.path.isfile(file_path):
        return "File not found on the server.", 404

    # Record the access in the audit log
    try:
        db.session.add(
            AuditLog(
                user_email=session["email"],
                action="DOCUMENT_VIEW",
                document_id=document.id
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to record document access")
        return "Unable to record access. Document was not opened.", 500

    # Return the file only after authorization and logging
    from flask import send_file

    return send_file(
        file_path,
        as_attachment=False,
        download_name=document.original_name
    )
@app.route("/share-document/<int:document_id>", methods=["GET", "POST"])
def share_document(document_id):
    if "email" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Owner":
        return "Access denied.", 403

    document = db.session.get(Document, document_id)

    if document is None:
        return "Document not found.", 404

    if document.owner_email != session["email"]:
        return "Access denied.", 403

    message = ""

    if request.method == "POST":
        viewer_email = request.form.get("viewer_email", "").strip().lower()

        viewer = User.query.filter_by(email=viewer_email).first()

        if not viewer:
            message = "Viewer account not found."
        elif viewer.role != "Viewer":
            message = "You can share documents only with Viewer accounts."
        else:
            permission = DocumentPermission.query.filter_by(
                document_id=document.id,
                viewer_email=viewer_email
            ).first()

            if permission:
                permission.can_view = True
            else:
                permission = DocumentPermission(
                    document_id=document.id,
                    viewer_email=viewer_email,
                    can_view=True
                )
                db.session.add(permission)

            try:
                db.session.add(
                    AuditLog(
                        user_email=session["email"],
                        action="DOCUMENT_SHARE",
                        document_id=document.id
                    )
                )
                db.session.commit()
                message = "Document shared successfully."
            except Exception:
                db.session.rollback()
                app.logger.exception("Document sharing failed")
                message = "Unable to share the document. Please try again."

    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Share Document - TrustVault</title></head>
    <body style="font-family:Arial;background:#f1f5f9;padding:40px">
        <div style="background:white;padding:30px;border-radius:12px;max-width:500px;margin:auto">
            <h1>Share Document</h1>
            <p>Document: {document.original_name}</p>
            <p>{message}</p>

            <form method="POST">
                <label>Viewer email address:</label><br><br>
                <input type="email" name="viewer_email" required>
                <br><br>
                <button type="submit">Grant View Access</button>
            </form>
            <hr>
            <h3>Revoke Viewer Access</h3>
            <form method="POST" action="/revoke-access/{document.id}">
                <label>Viewer email address:</label><br><br>
                <input type="email" name="viewer_email" required>
                <br><br>
                <button type="submit">Revoke Access</button>
            </form>
            <br><a href="/my-documents">Back to My Documents</a>
        </div>
    </body>
    </html>
    """
@app.route("/shared-documents")
def shared_documents():
    if "email" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Viewer":
        return "Access denied.", 403

    permissions = DocumentPermission.query.filter_by(
        viewer_email=session["email"],
        can_view=True
    ).all()

    document_list = ""

    for permission in permissions:
        document = db.session.get(Document, permission.document_id)

        if document is not None:
            document_list += f"""
                <li>
                    <strong>{document.original_name}</strong>
                    <br>
                    <a href="/view-document/{document.id}">View Document</a>
                </li>
                <br>
            """

    if not document_list:
        document_list = "<p>No documents have been shared with you.</p>"

    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>My Shared Documents - TrustVault</title>
        </head>
        <body style="font-family:Arial;background:#f1f5f9;padding:40px">
            <div style="background:white;padding:30px;border-radius:12px;max-width:700px;margin:auto">
                <h1>My Shared Documents</h1>
                <p>Documents shared with your account:</p>
                <ul>{document_list}</ul>
                <a href="/dashboard">Back to Dashboard</a>
            </div>
        </body>
        </html>
    """

@app.route("/revoke-access/<int:document_id>", methods=["POST"])
def revoke_access(document_id):
    if "email" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Owner":
        return "Access denied.", 403

    document = db.session.get(Document, document_id)

    if document is None:
        return "Document not found.", 404

    if document.owner_email != session["email"]:
        return "Access denied.", 403

    viewer_email = request.form.get("viewer_email", "").strip().lower()

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        viewer_email=viewer_email,
        can_view=True
    ).first()

    if permission is None:
        return "No active permission found.", 404

    try:
        permission.can_view = False

        db.session.add(AuditLog(
            user_email=session["email"],
            action="DOCUMENT_REVOKE",
            document_id=document.id
        ))

        db.session.commit()

        return """
            <p>Access revoked successfully!</p>
            <a href="/my-documents">Back to My Documents</a>
        """
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to revoke document access")
        return "Unable to revoke access.", 500

@app.route("/admin-audit")
def admin_audit():
    if "email" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access denied.", 403

    logs = AuditLog.query.order_by(
        AuditLog.timestamp.desc()
    ).all()

    log_rows = ""

    for log in logs:
        log_rows += f"""
            <tr>
                <td>{log.user_email}</td>
                <td>{log.action}</td>
                <td>{log.document_id if log.document_id is not None else "-"}</td>
                <td>{log.timestamp}</td>
            </tr>
        """

    if not log_rows:
        log_rows = "<tr><td colspan='4'>No activity recorded yet.</td></tr>"

    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TrustVault Audit Logs</title>
        </head>
        <body style="font-family:Arial;background:#f1f5f9;padding:40px">
            <div style="background:white;padding:30px;border-radius:12px;max-width:1000px;margin:auto">
                <h1>TrustVault Audit Logs</h1>
                <p>Review recorded user activity.</p>
                <table border="1" cellpadding="10" cellspacing="0" width="100%">
                    <tr>
                        <th>User Email</th>
                        <th>Action</th>
                        <th>Document ID</th>
                        <th>Timestamp</th>
                    </tr>
                    {log_rows}
                </table>
                <br>
                <a href="/dashboard">Back to Dashboard</a>
            </div>
        </body>
        </html>
    """

    
if __name__ == "__main__":
    app.run(debug=True)