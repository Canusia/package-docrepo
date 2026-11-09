"""CE documents page: inline Add New panel (AJAX post with a file), the
drag-and-drop file input, and the Copy Links bulk action."""
from unittest import mock

from django.contrib.staticfiles import finders
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from cis.storage_backend import PrivateMediaStorage

from .models.model import DocRepo
from .test_access import SIGNED, _quiet_login_history, _user

AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class _CEPageTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ce = _user('cp_ce', 'ce')
        cls.student = _user('cp_student', 'student')

    def setUp(self):
        _quiet_login_history(self)
        for name in ('url', 'save'):
            patcher = mock.patch.object(
                PrivateMediaStorage, name,
                **({'return_value': SIGNED} if name == 'url'
                   else {'side_effect': lambda path, content, **kw: path}))
            patcher.start()
            self.addCleanup(patcher.stop)

    def _doc(self, title, available_to=('High School Administrators',)):
        return DocRepo.objects.create(
            title=title, description='x', media=f'docrepo/{title}/f.pdf',
            available_to=list(available_to), uploaded_by=self.ce)


class AddNewTests(_CEPageTestCase):

    def _post(self, data, ajax=True, user=None):
        self.client.force_login(user or self.ce)
        return self.client.post(
            reverse('docrepo:add_new'), data, **(AJAX if ajax else {}))

    def _data(self, **extra):
        data = {
            'title': 'Handbook', 'description': '<p>x</p>',
            'available_to': ['Students'], 'display_weight': 0,
            'media': SimpleUploadedFile('handbook.pdf', b'%PDF-1.4', 'application/pdf'),
        }
        data.update(extra)
        return data

    def test_ajax_post_saves_and_answers_json(self):
        response = self._post(self._data())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['status'], 'success')
        record = DocRepo.objects.get(title='Handbook')
        self.assertEqual(record.uploaded_by, self.ce)
        self.assertEqual(body['ce_url'], str(record.ce_url))

    def test_ajax_post_without_file_is_400_with_field_errors(self):
        data = self._data()
        del data['media']
        response = self._post(data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('media', response.json()['errors'])
        self.assertFalse(DocRepo.objects.filter(title='Handbook').exists())

    def test_plain_post_still_redirects_to_the_document(self):
        response = self._post(self._data(), ajax=False)
        record = DocRepo.objects.get(title='Handbook')
        self.assertRedirects(response, reverse('docrepo:doc', args=[record.id]),
                             fetch_redirect_response=False)

    def test_non_ce_cannot_add(self):
        response = self._post(self._data(), user=self.student)
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(DocRepo.objects.filter(title='Handbook').exists())

    def test_file_input_is_a_dropzone(self):
        from .forms.docrepo import DocRepoForm
        self.assertIn('data-dropzone', str(DocRepoForm()['media']))

    def test_standalone_page_loads_the_dropzone(self):
        self.client.force_login(self.ce)
        response = self.client.get(reverse('docrepo:add_new'))
        self.assertContains(response, 'docrepo/js/file_dropzone.js')

    def test_static_files_ship(self):
        for path in ('docrepo/js/file_dropzone.js', 'docrepo/js/copy_link.js'):
            self.assertIsNotNone(finders.find(path), path)


class DetailPageTests(_CEPageTestCase):

    def test_edit_without_a_file_keeps_it_and_with_one_replaces_it(self):
        doc = self._doc('Alpha')
        self.client.force_login(self.ce)
        url = reverse('docrepo:doc', args=[doc.id])
        data = {'title': 'Alpha 2', 'description': 'x', 'available_to': ['Students'],
                'display_weight': 0}
        self.client.post(url, data)
        doc.refresh_from_db()
        self.assertEqual((doc.title, doc.media.name), ('Alpha 2', 'docrepo/Alpha/f.pdf'))

        data['media'] = SimpleUploadedFile('new.pdf', b'%PDF-1.4', 'application/pdf')
        self.client.post(url, data)
        doc.refresh_from_db()
        self.assertTrue(doc.media.name.endswith('new.pdf'))

    def test_detail_page_uses_shared_copy_script(self):
        doc = self._doc('Alpha')
        self.client.force_login(self.ce)
        response = self.client.get(reverse('docrepo:doc', args=[doc.id]))
        self.assertContains(response, 'data-docrepo-copy="#docrepo_file_link"')
        self.assertContains(response, 'docrepo/js/copy_link.js')
        self.assertContains(response, 'enctype="multipart/form-data"')


class IndexPageTests(_CEPageTestCase):

    def test_index_has_add_new_panel_and_bulk_button(self):
        self.client.force_login(self.ce)
        response = self.client.get(reverse('docrepo:all'))
        self.assertContains(response, 'id="addNewItem"')
        self.assertContains(response, 'id="frm_add_new_item"')
        self.assertContains(response, 'data-dropzone')
        self.assertContains(response, 'docrepo/js/file_dropzone.js')
        self.assertContains(response, 'href="#addNewItem"')
        # bulk button comes from the registry, and the select column sends a real key
        self.assertContains(response, "slug: 'copy_links'")
        self.assertContains(response, reverse('docrepo:bulk_actions'))
        self.assertContains(response, "data: 'id'")


class CopyLinksTests(_CEPageTestCase):

    def _post(self, data, user=None):
        self.client.force_login(user or self.ce)
        return self.client.post(reverse('docrepo:bulk_actions'), data)

    def test_unknown_action_is_400(self):
        self.assertEqual(self._post({'action': 'nope'}).status_code, 400)

    def test_get_is_405(self):
        self.client.force_login(self.ce)
        response = self.client.get(reverse('docrepo:bulk_actions'), {'action': 'copy_links'})
        self.assertEqual(response.status_code, 405)

    def test_non_ce_is_refused(self):
        doc = self._doc('a')
        response = self._post({'action': 'copy_links', 'ids[]': [doc.id]}, user=self.student)
        self.assertNotEqual(response.status_code, 200)

    def test_modal_lists_absolute_permanent_links(self):
        a, b = self._doc('Alpha'), self._doc('Beta', available_to=['Students'])
        response = self._post({'action': 'copy_links',
                               'ids[]': [a.id, b.id, 'not-a-uuid']})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['outcome'], 'modal')
        html = body['html']
        self.assertIn(f'http://testserver/documents/file/{a.id}/', html)
        self.assertIn(f'http://testserver/documents/file/{b.id}/', html)
        self.assertIn('Alpha', html)
        self.assertIn('data-docrepo-copy', html)
        # Beta isn't shared with HS admins, so it carries the note
        self.assertIn('High School Administrators', html)
        self.assertNotIn(SIGNED, html)

    def test_no_permanent_links_never_falls_back_to_signed_url(self):
        doc = self._doc('Alpha')
        with mock.patch.object(DocRepo, 'file_link', new_callable=mock.PropertyMock,
                               return_value=None):
            html = self._post({'action': 'copy_links', 'ids[]': [doc.id]}).json()['html']
        self.assertIn('not available', html)
        self.assertNotIn(SIGNED, html)


class FormAssetsTests(_CEPageTestCase):
    """The form has a field named "media", so {{ form.media }} in a template
    renders the file field again instead of the TinyMCE scripts."""

    def test_pages_load_tinymce_and_render_one_file_input(self):
        doc = self._doc('Alpha')
        self.client.force_login(self.ce)
        for url in (reverse('docrepo:all'), reverse('docrepo:add_new'),
                    reverse('docrepo:doc', args=[doc.id])):
            html = self.client.get(url).content.decode()
            self.assertIn('tinymce/tinymce.min.js', html, url)
            self.assertEqual(html.count('name="media"'), 1, url)

    def test_new_document_prompt_is_not_replacement(self):
        from .forms.docrepo import DocRepoForm
        self.assertIn('Drag the document here', str(DocRepoForm()['media']))
        doc = self._doc('Alpha')
        self.assertIn('replacement', str(DocRepoForm(instance=doc)['media']))
