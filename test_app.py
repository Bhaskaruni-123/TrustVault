
import unittest

from app import app
from database import AuditLog,db


class TrustVaultTests(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        with self.client.session_transaction() as session:
            session.clear()
        from database import db
        with app.app_context():
            db.session.remove()

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)

    def test_admin_audit_requires_login(self):
        response = self.client.get("/admin-audit")
        self.assertEqual(response.status_code, 302)

    def test_viewer_cannot_open_admin_audit(self):
        with self.client.session_transaction() as session:
            session["email"] = "viewer@trustvault.com"
            session["role"] = "Viewer"

        response = self.client.get("/admin-audit")
        self.assertEqual(response.status_code, 403)


    def test_viewer_cannot_upload_document(self):
        with self.client.session_transaction() as session:
            session["email"] = "viewer@trustvault.com"
            session["role"] = "Viewer"

        response = self.client.get("/upload")
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_access_owner_documents(self):
        with self.client.session_transaction() as session:
            session["email"] = "viewer@trustvault.com"
            session["role"] = "Viewer"

        response = self.client.get("/my-documents")
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_open_document_without_permission(self):
        with self.client.session_transaction() as session:
            session["email"] = "noaccess-test@example.com"
            session["role"] = "Viewer"

        response = self.client.get("/view-document/1")

        self.assertEqual(response.status_code, 403)

    def test_unauthorized_document_access_is_not_logged_as_view(self):
        with self.client.session_transaction() as session:
            session["email"] = "noaccess-test@example.com"
            session["role"] = "Viewer"

        response = self.client.get("/view-document/1")
        self.assertEqual(response.status_code, 403)

        with app.app_context():
            log = AuditLog.query.filter_by(
                user_email="noaccess-test@example.com",
                action="DOCUMENT_VIEW",
                document_id=1
            ).first()

            self.assertIsNone(log)

    def test_owner_document_view_is_logged(self):
        with self.client.session_transaction() as session:
            session["email"] = "owner@trustvault.com"
            session["role"] = "Owner"

        with app.app_context():
            from database import Document

            document = Document.query.filter_by(
                original_name="test.txt",
                owner_email="owner@trustvault.com"
            ).first()

            self.assertIsNotNone(document)
            document_id = document.id

        response = self.client.get(
            f"/view-document/{document_id}"
        )

        self.assertEqual(response.status_code, 200)
        response.close()

        with app.app_context():
            log = AuditLog.query.filter_by(
                user_email="owner@trustvault.com",
                action="DOCUMENT_VIEW",
                document_id=document_id
            ).order_by(AuditLog.id.desc()).first()

            self.assertIsNotNone(log)

    def test_admin_cannot_open_document_without_permission(self):
        with self.client.session_transaction() as session:
            session["email"] = "admin@trustvault.com"
            session["role"] = "Admin"

        response = self.client.get("/view-document/1")
        self.assertEqual(response.status_code, 403)
        response.close()

    def test_owner_can_share_document_with_viewer(self):
        with app.app_context():
            from database import Document, DocumentPermission

            document = Document.query.filter_by(
                original_name="test.txt",
                owner_email="owner@trustvault.com"
            ).first()

            self.assertIsNotNone(document)
            document_id = document.id

            permission = DocumentPermission.query.filter_by(
                document_id=document_id,
                viewer_email="viewer@trustvault.com"
            ).first()

            if permission:
                permission.can_view = False
                db.session.commit()

        with self.client.session_transaction() as session:
            session["email"] = "owner@trustvault.com"
            session["role"] = "Owner"

        response = self.client.post(
            f"/share-document/{document_id}",
            data={"viewer_email": "viewer@trustvault.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Document shared successfully", response.data)

        with app.app_context():
            permission = DocumentPermission.query.filter_by(
                document_id=document_id,
                viewer_email="viewer@trustvault.com",
                can_view=True
            ).first()

            self.assertIsNotNone(permission)

    def test_authorized_viewer_can_open_shared_document(self):
        with app.app_context():
            from database import Document, DocumentPermission

            document = Document.query.filter_by(
                original_name="test.txt",
                owner_email="owner@trustvault.com"
            ).first()

            self.assertIsNotNone(document)
            document_id = document.id

            permission = DocumentPermission.query.filter_by(
                document_id=document_id,
                viewer_email="viewer@trustvault.com"
            ).first()

            if permission:
                permission.can_view = True
            else:
                permission = DocumentPermission(
                    document_id=document_id,
                    viewer_email="viewer@trustvault.com",
                    can_view=True
                )
                db.session.add(permission)

            db.session.commit()

        with self.client.session_transaction() as session:
            session["email"] = "viewer@trustvault.com"
            session["role"] = "Viewer"

        response = self.client.get(
            f"/view-document/{document_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"TrustVault test document", response.data)
        response.close()


    def test_owner_can_revoke_viewer_access(self):
        with app.app_context():
            from database import Document, DocumentPermission

            document = Document.query.filter_by(
                original_name="test.txt",
                owner_email="owner@trustvault.com"
            ).first()

            self.assertIsNotNone(document)
            document_id = document.id

            permission = DocumentPermission.query.filter_by(
                document_id=document_id,
                viewer_email="viewer@trustvault.com"
            ).first()

            if permission:
                permission.can_view = True
            else:
                permission = DocumentPermission(
                    document_id=document_id,
                    viewer_email="viewer@trustvault.com",
                    can_view=True
                )
                db.session.add(permission)

            db.session.commit()

        with self.client.session_transaction() as session:
            session["email"] = "owner@trustvault.com"
            session["role"] = "Owner"

        response = self.client.post(
            f"/revoke-access/{document_id}",
            data={"viewer_email": "viewer@trustvault.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Access revoked successfully", response.data)

        with app.app_context():
            permission = DocumentPermission.query.filter_by(
                document_id=document_id,
                viewer_email="viewer@trustvault.com",
                can_view=True
            ).first()

            self.assertIsNone(permission)
    def test_viewer_cannot_share_document(self):
        with self.client.session_transaction() as session:
            session["email"] = "viewer@trustvault.com"
            session["role"] = "Viewer"

        response = self.client.post(
            "/share-document/1",
            data={"viewer_email": "viewer@trustvault.com"}
        )

        self.assertEqual(response.status_code, 403)
        response.close()
    def test_viewer_cannot_revoke_access(self):
        with self.client.session_transaction() as session:
            session["email"] = "viewer@trustvault.com"
            session["role"] = "Viewer"

        response = self.client.post(
            "/revoke-access/1",
            data={"viewer_email": "viewer@trustvault.com"}
        )

        self.assertEqual(response.status_code, 403)
        response.close()
    def test_upload_rejects_unsupported_file_type(self):
        from io import BytesIO

        with self.client.session_transaction() as session:
            session["email"] = "owner@trustvault.com"
            session["role"] = "Owner"

        response = self.client.post(
            "/upload",
            data={
                "document": (
                    BytesIO(b"harmless test content"),
                    "test.exe"
                )
            },
            content_type="multipart/form-data"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"File type not allowed", response.data)
        response.close()
if __name__ == "__main__":
    unittest.main()
