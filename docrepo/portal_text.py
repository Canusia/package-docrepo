"""Portal page text ("blurbs"), read from whichever app owns it.

The instructor and faculty portal text is moving out of cis into the portal
packages (package-cis#81, #82). Each role's sources, most preferred first: the
package's nested editable layout, its installed layout, then cis's copy, so
this works on tenants on either side of the move.

Availability is checked with ``find_spec`` rather than ``try/except ImportError``
so that a real import error inside a present module still raises.
"""
import importlib
import importlib.util

PORTAL_TEXT_SOURCES = {
    'instructor': (
        ('instructor.instructor.settings.instructor_portal', 'instructor_portal'),
        ('instructor.settings.instructor_portal', 'instructor_portal'),
        ('cis.settings.instructor_portal', 'instructor_portal'),
    ),
    'faculty': (
        ('faculty.faculty.settings.faculty_portal_text', 'faculty_portal_text'),
        ('faculty.settings.faculty_portal_text', 'faculty_portal_text'),
        ('cis.settings.faculty_portal', 'faculty_portal'),
    ),
}


def has_module(name):
    """True when the dotted module ``name`` is importable."""
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:  # a parent package is missing
        return False


def portal_text(role):
    """The stored page text for the ``role`` portal, or {} when nothing owns it."""
    for module, attr in PORTAL_TEXT_SOURCES[role]:
        if has_module(module):
            value = getattr(importlib.import_module(module), attr).from_db()
            return value if isinstance(value, dict) else {}
    return {}


#: Per role, the label the docrepo item is registered with (menu.py and the
#: _menu_item decorators in views.py). Only that role's own label counts as
#: "not renamed", so renaming e.g. the instructor item to "Documents" works.
STOCK_LABELS = {
    'ce': {'Documents'},
    'faculty': {'Documents Library'},
    'instructor': {'Shared Docs.'},
    'highschool_admin': {'Documents'},
    'student': {'Documents'},
}


# A copy of cis.portal_text._find_item for cis versions without it.
def _find_item(items, name):
    stack = list(items or ())
    while stack:
        item = stack.pop(0)
        if not isinstance(item, dict):
            continue
        if item.get('name') == name:
            return item
        stack.extend(item.get('sub_menu') or ())
    return None


def page_heading(role, default, name='docrepo'):
    """The label CE gave ``role``'s Documents menu item, else ``default`` (#3).

    Uses ``cis.portal_text.page_heading`` (cis v0.2.10a+) when present, else
    reads the role menu directly; any failure returns ``default`` so the page
    always renders.
    """
    try:
        from cis.portal_text import page_heading as cis_heading
    except Exception:
        cis_heading = None
    if cis_heading is not None:
        try:
            heading = cis_heading(role, name, default)
        except Exception:
            return default
        return default if heading in STOCK_LABELS.get(role, ()) else heading
    try:
        from cis.menu import get_role_menu
        item = _find_item(get_role_menu(role, visible_only=False), name)
    except Exception:
        return default
    label = item.get('label') if item else None
    if (not isinstance(label, str) or not label.strip()
            or label.strip() in STOCK_LABELS.get(role, ())):
        return default
    return label.strip()
