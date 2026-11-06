"""The docrepo package's sidebar items are in the cis menu registry (menu.py, from ready()).

Ids are the legacy menu names; `<id>_blurb` portal-text fields,
`active_menu` values and converted layouts' `adopt` paths depend on them.
"""
import importlib.util
import unittest

from django.test import SimpleTestCase

HAS_REGISTRY = importlib.util.find_spec('cis.menu_registry') is not None
SOURCE = 'docrepo'

EXPECTED = {
    'ce': {'docrepo': ('Documents', 'docrepo:all', 130)},
    'faculty': {'docrepo': ('Documents Library', 'faculty_docrepo:docs', 70)},
    'instructor': {'docrepo': ('Shared Docs.', 'instructor_docrepo:docs', 80)},
    'student': {'docrepo': ('Documents', 'student_docrepo:docs', 55)},
    'highschool_admin': {'docrepo': ('Documents', 'highschool_admin_docrepo:docs', 105)},
}

#: Items added after the menu registry shipped start hidden; CE turns them on.
HIDDEN = {('student', 'docrepo'), ('highschool_admin', 'docrepo')}

#: Every portal landing page the package exposes, by role (url name).
LANDING_PAGES = {
    'ce': ['docrepo:all'],
    'faculty': ['faculty_docrepo:docs'],
    'instructor': ['instructor_docrepo:docs'],
    'student': ['student_docrepo:docs'],
    'highschool_admin': ['highschool_admin_docrepo:docs'],
}


def _paths(role):
    from cis.menu_registry import menu
    out = {}
    for item in menu.items(role):
        if item['source'] == SOURCE:
            out[item['name']] = item
        for sub in item['sub_menu']:
            if sub.get('source') == SOURCE and sub['type'] == 'nav-item':
                out[f"{item['name']}/{sub['name']}"] = sub
    return out


@unittest.skipUnless(HAS_REGISTRY, 'cis has no menu registry')
class MenuItemsTests(SimpleTestCase):

    def test_items_registered(self):
        for role, expected in EXPECTED.items():
            got = {path: (i['label'], i['url'], i['order'])
                   for path, i in _paths(role).items()}
            self.assertEqual(got, expected, role)

    def test_no_registry_problems(self):
        from cis.menu_registry import check_menu_registry, menu
        problems = [m for m in check_menu_registry(menu)
                    if m.id.startswith('cis.E_MENU') and f'({SOURCE})' in m.msg]
        self.assertEqual(problems, [])

    def test_new_items_start_hidden(self):
        for role, expected in EXPECTED.items():
            for path, item in _paths(role).items():
                self.assertEqual(item['default_visible'],
                                 (role, path) not in HIDDEN, (role, path))

    def test_every_landing_page_has_a_menu_item(self):
        for role, url_names in LANDING_PAGES.items():
            urls = {i['url'] for i in _paths(role).values()}
            for url_name in url_names:
                self.assertIn(url_name, urls, role)
