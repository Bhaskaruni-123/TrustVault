# TrustVault — Threat Model

## 1. Purpose

TrustVault protects confidential documents by restricting access to authorized users and recording important document-related actions. This document describes key threats, existing controls, and remaining risks.

## 2. Assets to Protect

- Confidential documents and their contents.
- User credentials and login sessions.
- Document ownership and sharing permissions.
- Audit logs containing access history.
- Application secrets and database records.

## 3. Threats and Mitigations

### Threat 1: Unauthorized Document Access

**Risk:** A user attempts to open a document without permission.

**Mitigation:** The server checks authentication, document ownership, user role, and explicit viewer permissions before serving a document.

**Remaining risk:** Authorization logic must be tested whenever routes or permissions change.

### Threat 2: Excessive Permissions

**Risk:** A viewer receives access to documents they do not need.

**Mitigation:** Owners share individual documents with specific viewer accounts and can revoke access.

**Remaining risk:** Incorrect sharing decisions by authorized owners remain possible.

### Threat 3: Malicious File Uploads

**Risk:** An attacker uploads an unexpected file type.

**Mitigation:** The application restricts file extensions, sanitizes filenames, generates unique storage names, and limits upload size.

**Remaining risk:** Extension checks do not prove that file contents are safe. Content validation, malware scanning, and stronger upload controls may be needed.

### Threat 4: Credential Compromise

**Risk:** An attacker obtains a user's password or session.

**Mitigation:** Passwords are stored as password hashes, and authenticated routes use server-side session checks.

**Remaining risk:** Production deployment requires a strong secret key, HTTPS, secure cookie settings, and appropriate password and session protections.

### Threat 5: Unauthorized Permission Changes

**Risk:** A viewer attempts to share documents or revoke another user's access.

**Mitigation:** The server restricts sharing and revocation to owners and checks document ownership.

**Remaining risk:** All new permission-changing routes must apply equivalent authorization checks.

### Threat 6: Audit Log Tampering or Missing Events

**Risk:** Important document activity is not recorded or audit records are altered.

**Mitigation:** The application records login, logout, upload, view, share, and revoke events.

**Remaining risk:** The current database audit log is not a tamper-proof external record. Stronger deployments should restrict log modification and consider centralized or append-only logging.

### Threat 7: Database or Storage Exposure

**Risk:** An attacker obtains direct access to stored documents or database files.

**Mitigation:** Uploaded documents are stored in a private application directory rather than a public static directory.

**Remaining risk:** Server access, backups, filesystem permissions, and deployment storage must be secured.

### Threat 8: Cross-Site Scripting (XSS) and Request Forgery

**Risk:** Unsafe user-controlled content executes in a user's browser, or an authenticated user is tricked into submitting an unwanted action.

**Mitigation:** User-controlled output must be safely escaped, and state-changing forms should use CSRF protection.

**Remaining risk:** These protections require a complete code review and verification before production deployment.

## 4. Security Testing

The automated test suite checks role restrictions, unauthorized document access, sharing and revocation rules, audit behavior, and unsupported upload extensions. Manual tests have also verified rejection of an unsupported extension and successful upload of a text file.

## 5. Production Security Checklist

- Configure a strong, private application secret key.
- Disable Flask debug mode.
- Use HTTPS and secure session-cookie settings.
- Validate upload extensions and actual file contents.
- Keep private documents outside public static directories.
- Review authentication, authorization, and CSRF protection.
- Protect audit logs and database backups.
- Store production data persistently and restrict server access.
- Run automated tests before deployment.

## 6. Scope and Limitations

This threat model documents the current design and known limitations. It does not claim that all threats have been eliminated. Security depends on implementation details, configuration, testing, and the production environment.