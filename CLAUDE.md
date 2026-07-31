# docrepo — MyCE Shared Document Repository

Django app providing the CE-managed shared document library for the MyCE platform.

## Package Info

- Package name: `myce_docrepo`
- Installed as: `docrepo` (production, pip) / `docrepo.docrepo` (dev, editable submodule)
- App configs: `docrepo.apps.DocRepoConfig` (prod), `docrepo.docrepo.apps.DevDocRepoConfig` (dev)
- Django app label: **`docrepo` in both layouts** — never set an explicit `label`, and never
  rename the inner directory. The label backs the `docrepo_docrepo` table and the applied
  `('docrepo', '0001_initial')` migration row on every existing deployment.

## Structure

```
docrepo/            ← Django app
  apps.py           ← DocRepoConfig (prod) + DevDocRepoConfig (dev)
  models/model.py   ← DocRepo model (UUID pk, PrivateMediaStorage FileField)
  forms/docrepo.py  ← DocRepoForm
  views/views.py    ← CE CRUD + per-role read-only lists + DocRepoViewSet
  serializers.py    ← DocRepoSerializer (DataTables)
  urls/
    ce.py                ← app_name 'docrepo'
    student.py           ← app_name 'student_docrepo'
    instructor.py        ← app_name 'instructor_docrepo'
    faculty.py           ← app_name 'faculty_docrepo'
    highschool_admin.py  ← app_name 'highschool_admin_docrepo' (not mounted by EWU)
  templates/docrepo/
    index.html, details.html, add_new.html, links.html
    student/index.html            ← reused by student, instructor, faculty, HS admin
    highschool_admin/*.html
  migrations/0001_initial.py
```

## Key Concepts

### Model
`DocRepo` — UUID pk; `title`, `description` (TinyMCE `HTMLField`), `available_to`
(`MultiSelectField`: Students / High School Administrators / Instructors / Faculty),
`display_weight`, `media` (`FileField` on `cis.storage_backend.PrivateMediaStorage`,
uploaded to `docrepo/<id>/<filename>`), `uploaded_by`, `uploaded_on`.

`ce_url` is a property returning `reverse_lazy('docrepo:doc', …)`; the serializer exposes it
via `datatables_always_serialize`, so the CE namespace `docrepo` must stay mounted.

### Role filtering
`get_documents(request, user_role)` maps a role string to the matching `available_to` value and
filters on `available_to__contains`, ordered by `display_weight`. Note `DocRepoViewSet` is a
`ReadOnlyModelViewSet` that returns **all** documents with no role filter — it is only mounted
under the CE prefix, which is `user_has_cis_role`-gated at the view layer.

### Portal blurb
The per-portal intro text comes from the host's `cis.settings.*_portal` setting under the key
`docrepo_blurb`. That setting lives in the host (`cis`), not in this package.

### Dev vs Production
All intra-package imports are **relative** (`from ..models.model import DocRepo`). An absolute
`from docrepo.models…` resolves only in the 2-deep dev layout and breaks the pip install — this
is the exact bug that had to be fixed after the `class_visit` extraction.

## Host requirements
- `INSTALLED_APPS` entry via the `find_spec('docrepo.docrepo')` conditional.
- Four URL includes (`ce`, `instructor`, `student`, `faculty`) via a `_dr` prefix alias.
- The package ships **no** `staticfiles/` directory — nothing to add to `STATICFILES_DIRS`.
- Depends on host app `cis` for `storage_backend`, `utils` role predicates, `menu`, and
  `settings.*_portal`.
