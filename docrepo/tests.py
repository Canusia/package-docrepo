from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from .models.model import DocRepo


class DocRepoPackagingTests(TestCase):
    """Guards the invariants that make the submodule swap a code-move only."""

    def test_app_label_is_docrepo_in_either_layout(self):
        self.assertEqual(DocRepo._meta.app_label, 'docrepo')

    def test_db_table_is_unchanged(self):
        self.assertEqual(DocRepo._meta.db_table, 'docrepo_docrepo')

    def test_app_config_is_registered(self):
        config = apps.get_app_config('docrepo')
        self.assertIn(config.name, ('docrepo', 'docrepo.docrepo'))

    def test_upload_path_is_stable(self):
        from .models.model import docrepo_upload_path
        record = DocRepo(title='x')
        record.id = 'abc'
        self.assertEqual(docrepo_upload_path(record, 'f.pdf'), 'docrepo/abc/f.pdf')


class DocRepoUrlTests(TestCase):
    """The URL namespaces are public surface — they must not move."""

    def test_ce_namespace(self):
        self.assertEqual(reverse('docrepo:all'), '/ce/documents/')
        self.assertEqual(reverse('docrepo:add_new'), '/ce/documents/document/add_new')

    def test_portal_namespaces(self):
        self.assertEqual(reverse('student_docrepo:docs'), '/student/documents/')
        self.assertEqual(reverse('instructor_docrepo:docs'), '/instructor/documents/')
        self.assertEqual(reverse('faculty_docrepo:docs'), '/faculty/documents/')

    def test_ce_templates_are_shipped(self):
        from django.template.loader import get_template
        for name in (
            'docrepo/index.html',
            'docrepo/details.html',
            'docrepo/add_new.html',
            'docrepo/student/index.html',
        ):
            self.assertIsNotNone(get_template(name))
