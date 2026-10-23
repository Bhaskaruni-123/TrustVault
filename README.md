# TrustVault 🔐
## Secure Document Sharing with an Audit Trail

TrustVault is a secure document-sharing web application built using Python and Flask. It helps prevent unauthorized access to confidential documents through role-based access control and document-specific permissions.

## Features

- User login and session management.
- Three roles: Administrator, Document Owner, and Viewer.
- Secure document uploads with file-type restrictions.
- Private document storage.
- Document sharing with authorized viewers.
- Document access revocation.
- Server-side permission checks.
- Audit logs for login, logout, upload, view, share, and revoke actions.
- Automated tests for important security rules.

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML and CSS
- Python unittest

## Project Structure

- `app.py` — Flask application and routes.
- `database.py` — Database models.
- `init_db.py` — Database initialization script.
- `test_app.py` — Automated tests.
- `private_documents/` — Private uploaded documents.
- `THREATS.md` — Security risks and mitigations.
- `PROMPTS.md` — AI-assisted development record.

## Requirements

- Python 3
- pip

## Installation

1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Create a virtual environment:

   `python -m venv venv`

4. Activate it on Windows:

   `venv\Scripts\activate`

5. Install the dependencies:

   `pip install Flask Flask-SQLAlchemy`

## Run the Application

Start the development server:

`python app.py`

Open your browser and visit:

`http://127.0.0.1:5000`

## Run Automated Tests

Run:

`python -m unittest test_app.py -v`

The tests cover authentication, role restrictions, document access, sharing, revocation, audit logging, and upload validation.

## Roles and Permissions

- **Administrator:** Can access the audit-log page.
- **Document Owner:** Can upload documents, manage owned documents, share them with viewers, and revoke access.
- **Viewer:** Can view documents only when explicitly granted permission.

Permissions are checked on the server, not just in the interface.

## Security Notes

- Uploaded files use generated storage names.
- Uploads have a size limit and an allowed-extension check.
- Documents are stored outside public static-file access.
- Unauthorized document access is rejected.
- Audit events are recorded for important actions.

The extension check alone does not verify a file's actual contents. Review `THREATS.md` for additional security limitations and mitigations.

## Testing Status

The project currently has 16 automated tests passing in the local development environment.

## Production Deployment

Before production deployment, configure a strong secret key, disable Flask debug mode, use HTTPS, configure persistent private storage and a production database as appropriate, and review all security settings.

## Author

Developed as part of the TrustVault hiring challenge.