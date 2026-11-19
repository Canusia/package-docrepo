"""Portal Documents pages follow the menu label CE set (#3).

RVC renamed the HS admin item to "Blank Forms"; the page title and
breadcrumb must match. With no rename each page keeps its old text.
"""
import sys
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from . import portal_text
from .test_access import _quiet_login_history, _user
from .views import views


def _cis_heading(registered):
    """Mimics cis.portal_text.page_heading: ``default`` when the saved label
    is missing or the role's registered one."""
    def heading(saved):
        return lambda role, name, default: (
            default if not saved or saved == registered else saved)
    return heading


class CisHelperPathTests(SimpleTestCase):
    def _heading(self, role, saved, registered, default=None):
        with mock.patch('cis.portal_text.page_heading',
                        _cis_heading(registered)(saved), create=True):
            return portal_text.page_heading(role, default)

    def test_renamed_label_is_used(self):
        self.assertEqual(
            self._heading('highschool_admin', 'Blank Forms', 'Documents'),
            'Blank Forms')

    def test_own_registered_label_is_not_a_rename(self):
        for role, label in (('faculty', 'Documents Library'),
                            ('instructor', 'Shared Docs.'),
                            ('highschool_admin', 'Documents')):
            self.assertIsNone(self._heading(role, label, 'x'), role)

    def test_another_roles_stock_label_is_a_rename(self):
        # Instructor renamed "Shared Docs." -> "Documents".
        self.assertEqual(
            self._heading('instructor', 'Documents', 'Shared Docs.'),
            'Documents')

    def test_cis_helper_error_falls_back_to_default(self):
        def boom(role, name, default):
            raise RuntimeError('menu')
        with mock.patch('cis.portal_text.page_heading', boom, create=True):
            self.assertEqual(
                portal_text.page_heading('student', 'Documents'), 'Documents')


class OldCisFallbackTests(SimpleTestCase):
    """cis < v0.2.10a: no cis.portal_text.page_heading; read the menu."""

    def _heading(self, role, menu, default=None):
        with mock.patch.dict(sys.modules, {'cis.portal_text': None}), \
                mock.patch('cis.menu.get_role_menu', menu, create=True):
            return portal_text.page_heading(role, default)

    @staticmethod
    def _menu(label):
        return lambda role, visible_only=True: [
            {'name': 'group', 'sub_menu': [{'name': 'docrepo', 'label': label}]}]

    def test_nested_renamed_label_is_found_and_stripped(self):
        self.assertEqual(
            self._heading('highschool_admin', self._menu('  Blank Forms ')),
            'Blank Forms')

    def test_stock_blank_or_missing_label_gives_default(self):
        for menu in (self._menu('Documents'), self._menu(''), self._menu(None),
                     lambda role, visible_only=True: []):
            self.assertEqual(
                self._heading('highschool_admin', menu, 'D'), 'D')

    def test_menu_error_gives_default(self):
        def old_signature(role):   # pre-visible_only cis -> TypeError
            return []
        self.assertEqual(
            self._heading('faculty', old_signature, 'D'), 'D')


class BreadcrumbTests(SimpleTestCase):
    def test_breadcrumb_escapes_label(self):
        html = views._breadcrumb('/highschool_admin/', '<b>Forms</b>')
        self.assertIn('&lt;b&gt;Forms&lt;/b&gt;', html)
        self.assertIn('href="/highschool_admin/"', html)


class PortalPageRenderTests(TestCase):
    """The four portal pages, end to end."""

    @classmethod
    def setUpTestData(cls):
        cls.users = {role: _user(f'dph_{role}', role) for role in
                     ('faculty', 'instructor', 'highschool_admin', 'student')}

    def setUp(self):
        _quiet_login_history(self)

    def _get(self, role, renamed=None):
        self.client.force_login(self.users[role])
        with mock.patch.object(portal_text, 'page_heading',
                               lambda r, d, name='docrepo': renamed or d):
            return self.client.get(reverse(f'{role}_docrepo:docs'))

    def _crumb(self, label):
        return f'<li class="breadcrumb-item active" aria-current="page">{label}</li>'

    def test_defaults_are_unchanged(self):
        for role, crumb in (('faculty', 'Shared Docs.'),
                            ('instructor', 'Shared Docs.'),
                            ('highschool_admin', 'Documents')):
            response = self._get(role)
            self.assertEqual(response.status_code, 200, role)
            self.assertContains(response, self._crumb(crumb), html=False)
            self.assertEqual(response.context['page_title'], 'Documents', role)
        self.assertEqual(self._get('student').context['page_title'], 'Documents')

    def test_rename_sets_title_and_breadcrumb(self):
        response = self._get('highschool_admin', renamed='Blank Forms')
        self.assertContains(response, self._crumb('Blank Forms'), html=False)
        self.assertEqual(response.context['page_title'], 'Blank Forms')
        self.assertEqual(
            self._get('student', renamed='Blank Forms').context['page_title'],
            'Blank Forms')
