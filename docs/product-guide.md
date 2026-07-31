# Document Repository — Product Guide

## What it does

CE staff maintain a single library of shared documents (handbooks, forms, policy PDFs).
Each document is tagged with the portal roles allowed to see it. Those roles then see a
read-only, download-only list in their own portal.

## Roles

| Role | Sees | URL |
|---|---|---|
| CE administrator | Full CRUD over every document | `/ce/documents/` |
| Instructor | Documents tagged *Instructors* | `/instructor/documents/` |
| Faculty | Documents tagged *Faculty* | `/faculty/documents/` |
| Student | Documents tagged *Students* | `/student/documents/` |
| High school admin | Documents tagged *High School Administrators* | not mounted by default |

## CE workflow

1. **Documents** in the CE sidebar → the library list.
2. **Add New** → title, file, description, *Available To* roles, display weight.
3. The file is stored privately on S3 (`PrivateMediaStorage`) under `docrepo/<uuid>/<filename>`.
4. Documents render to portals ordered by **display weight** ascending.

## Notes and known gaps

- The DRF list endpoint (`/ce/documents/api/`) returns all documents with no role filter. It is
  mounted only under the CE prefix; role filtering happens in the server-rendered views.
- The high-school-admin URLconf and templates ship with the package but the EWU host does not
  mount them.
- The student nav entry is commented out in the host's default CE menu JSON; the route is live.
