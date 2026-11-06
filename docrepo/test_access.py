"""Permanent file links (docrepo_files:open), role document lists, and the
HS admin Documents page."""
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from cis.storage_backend import PrivateMediaStorage

from .access import can_open
from .models.model import DocRepo
from .views.views import get_documents

User = get_user_model()
SIGNED = 'https://bucket.example.com/private/docrepo/f.pdf?sig=1'


def _quiet_login_history(test):
    """django_login_history's receiver crashes on the test client's missing
    REMOTE_ADDR; drop the receivers for the test."""
    from django.contrib.auth.signals import user_logged_in
    saved = list(user_logged_in.receivers)
    user_logged_in.receivers = []

    def restore():
        user_logged_in.receivers = saved
    test.addCleanup(restore)


def _user(name, *roles):
    user = User.objects.create_user(
        username=name, email=f'{name}@example.com', password='x')
    for role in roles:
        user.groups.add(Group.objects.get_or_create(name=role)[0])
    return user


class FileLinkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ce = _user('dr_ce', 'ce')
        cls.student = _user('dr_student', 'student')
        cls.hsadmin = _user('dr_hsadmin', 'highschool_admin')
        cls.both = _user('dr_both', 'instructor', 'highschool_admin')
        cls.doc = DocRepo.objects.create(
            title='Name change form', description='x', media='docrepo/a/f.pdf',
            available_to=['High School Administrators'], uploaded_by=cls.ce)

    def setUp(self):
        _quiet_login_history(self)
        patcher = mock.patch.object(PrivateMediaStorage, 'url', return_value=SIGNED)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _get(self, user, record_id=None):
        if user:
            self.client.force_login(user)
        return self.client.get(
            reverse('docrepo_files:open', args=[record_id or self.doc.id]))

    def test_url_is_stable(self):
        self.assertEqual(
            reverse('docrepo_files:open', args=[self.doc.id]),
            f'/documents/file/{self.doc.id}/')

    def test_ce_always_redirected_to_signed_url(self):
        response = self._get(self.ce)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], SIGNED)

    def test_role_in_available_to_is_redirected(self):
        self.assertEqual(self._get(self.hsadmin)['Location'], SIGNED)

    def test_any_matching_role_is_enough(self):
        self.assertEqual(self._get(self.both)['Location'], SIGNED)

    def test_role_not_in_available_to_is_forbidden(self):
        response = self._get(self.student)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'not shared with your role', response.content)

    def test_anonymous_goes_to_login(self):
        response = self._get(None)
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response['Location'], SIGNED)

    def test_unknown_document_is_404(self):
        import uuid
        self.assertEqual(self._get(self.ce, uuid.uuid4()).status_code, 404)

    def test_can_open_helper(self):
        self.assertTrue(can_open(self.ce, self.doc))
        self.assertTrue(can_open(self.hsadmin, self.doc))
        self.assertFalse(can_open(self.student, self.doc))

    def test_file_link_and_download_url(self):
        self.assertEqual(self.doc.file_link, f'/documents/file/{self.doc.id}/')
        self.assertEqual(self.doc.download_url, self.doc.file_link)

    def test_ce_detail_page_shows_absolute_link(self):
        self.client.force_login(self.ce)
        response = self.client.get(reverse('docrepo:doc', args=[self.doc.id]))
        self.assertContains(
            response, f'http://testserver/documents/file/{self.doc.id}/')
        self.assertContains(response, 'id="docrepo_copy_link"')
        self.assertNotContains(response, 'tick High School Administrators')

    def test_ce_detail_page_warns_when_not_shared_with_hs_admins(self):
        doc = DocRepo.objects.create(
            title='Student only', description='x', media='docrepo/b/f.pdf',
            available_to=['Students'], uploaded_by=self.ce)
        self.client.force_login(self.ce)
        response = self.client.get(reverse('docrepo:doc', args=[doc.id]))
        self.assertContains(response, 'tick High School Administrators')


class RoleDocumentListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ce = _user('drl_ce', 'ce')
        cls.hsadmin = _user('drl_hsadmin', 'highschool_admin')
        cls.hs_doc = DocRepo.objects.create(
            title='For admins', description='x', media='docrepo/c/f.pdf',
            available_to=['High School Administrators'], uploaded_by=cls.ce)
        cls.student_doc = DocRepo.objects.create(
            title='For students', description='x', media='docrepo/d/f.pdf',
            available_to=['Students'], uploaded_by=cls.ce)

    def setUp(self):
        _quiet_login_history(self)

    def test_hs_admin_documents(self):
        self.assertEqual(list(get_documents(None, 'highschool_admin')), [self.hs_doc])

    def test_unknown_role_is_empty(self):
        self.assertEqual(list(get_documents(None, 'nobody')), [])

    def test_hs_admin_page_lists_their_documents(self):
        self.client.force_login(self.hsadmin)
        with mock.patch.object(PrivateMediaStorage, 'url', return_value=SIGNED):
            response = self.client.get(reverse('highschool_admin_docrepo:docs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'For admins')
        self.assertNotContains(response, 'For students')
        self.assertContains(response, f'/documents/file/{self.hs_doc.id}/')


class CEApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ce = _user('dra_ce', 'ce')
        cls.student = _user('dra_student', 'student')
        DocRepo.objects.create(
            title='Any', description='x', media='docrepo/e/f.pdf',
            available_to=['Faculty'], uploaded_by=cls.ce)

    def setUp(self):
        _quiet_login_history(self)

    def _get(self, user):
        self.client.force_login(user)
        with mock.patch.object(PrivateMediaStorage, 'url', return_value=SIGNED):
            return self.client.get('/ce/documents/api/?format=json')

    def test_ce_can_list(self):
        self.assertEqual(self._get(self.ce).status_code, 200)

    def test_other_roles_cannot_list(self):
        self.assertEqual(self._get(self.student).status_code, 403)
