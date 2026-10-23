# TrustVault — AI-Assisted Development Log

## Purpose

AI tools were used as development assistants to understand requirements, implement features, explain code, and improve testing. All proposed changes were reviewed and tested locally.

## Entry 1 — Application Structure

**Date:** 2026-10-21

**Prompt:** Help me plan a Python Flask application for secure document sharing with Administrator, Owner, and Viewer roles.

**Outcome:** Developed the application structure using Flask, SQLAlchemy, SQLite, and role-based routes.

**Verification:** Ran the application locally and tested the login and dashboard pages.

## Entry 2 — Document Permissions

**Date:** 2026-10-21

**Prompt:** Help implement server-side document ownership checks, explicit viewer permissions, sharing, and access revocation.

**Outcome:** Added permission checks to document-viewing and permission-management routes.

**Verification:** Tested allowed and denied access using different roles.

## Entry 3 — Audit Logging

**Date:** 2026-10-22

**Prompt:** Help record important security events, including login, logout, document upload, view, share, and revoke actions.

**Outcome:** Added audit-log records for important application actions.

**Verification:** Logged in as an administrator and checked the audit-log page.

## Entry 4 — Access-Control Test Improvement

**Date:** 2026-10-23

**Prompt:** Help write automated tests to verify that viewers cannot access administrator functions, upload documents, or perform owner-only actions.

**Issue and correction:** Access-control behavior must be verified through server responses, not just by hiding links in the interface. Tests were added to check forbidden requests.

**Verification:** Ran `python -m unittest test_app.py -v` and confirmed the existing test suite passed.

## Entry 5 — Upload Validation

**Date:** 2026-10-23

**Prompt:** Help restrict document uploads to an explicit list of file extensions and add an automated test for unsupported file types.

**Issue and correction:** Filename extension checks are useful but do not validate the actual file contents. The implementation was updated to reject unsupported extensions before saving the upload.

**Verification:** Manually tested rejection of a file named `test.exe` and successful upload of `test.txt`. Added an automated test for unsupported extensions and ran the test suite.

## Development Practices

- Reviewed AI suggestions before applying code changes.
- Tested changes locally using browser-based checks and automated tests.
- Prioritized server-side permission enforcement.
- Documented known security limitations rather than claiming complete protection.

## Important Note

This log summarizes the AI-assisted development workflow. Before submission, verify each entry against the actual project history and update any dates, prompts, or outcomes that do not accurately reflect the work performed.