from unittest import mock

from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from cis.models.settings import Setting

from . import portal_text
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


class PortalTextTests(TestCase):
    """portal_text: page text from the portal package when installed, else cis
    (package-cis#81/#82). Patching ``has_module`` stands in for a tenant without
    the package, or a cis that no longer ships its copy."""

    def _only(self, *present):
        sources = {m for role in portal_text.PORTAL_TEXT_SOURCES.values() for m, _ in role}
        real = portal_text.has_module
        return mock.patch.object(
            portal_text, 'has_module',
            side_effect=lambda name: name in present if name in sources else real(name))

    def setUp(self):
        Setting.objects.update_or_create(
            key='cis.settings.instructor_portal', defaults={'value': {'x_blurb': 'inst'}})
        Setting.objects.update_or_create(
            key='cis.settings.faculty_portal', defaults={'value': {'x_blurb': 'fac old', 'y_blurb': 'fac y'}})

    def test_instructor_text(self):
        self.assertEqual(portal_text.portal_text('instructor')['x_blurb'], 'inst')
        with self._only('cis.settings.instructor_portal'):
            self.assertEqual(portal_text.portal_text('instructor')['x_blurb'], 'inst')

    def test_faculty_cis_copy_without_the_package(self):
        Setting.objects.update_or_create(
            key='faculty.settings.faculty_portal', defaults={'value': {'x_blurb': 'fac new'}})
        with self._only('cis.settings.faculty_portal'):
            self.assertEqual(portal_text.portal_text('faculty')['x_blurb'], 'fac old')

    def test_faculty_package_copy_wins_per_key(self):
        if not any(portal_text.has_module(m) for m, _ in portal_text.PORTAL_TEXT_SOURCES['faculty'][:2]):
            self.skipTest('faculty package not installed')
        Setting.objects.update_or_create(
            key='faculty.settings.faculty_portal', defaults={'value': {'x_blurb': 'fac new'}})
        text = portal_text.portal_text('faculty')
        self.assertEqual((text['x_blurb'], text['y_blurb']), ('fac new', 'fac y'))

    def test_empty_when_nothing_owns_it(self):
        with self._only():
            self.assertEqual(portal_text.portal_text('instructor'), {})
            self.assertEqual(portal_text.portal_text('faculty'), {})
