"""Documents sidebar items (cis.menu_registry); id `docrepo` in every role.

On a cis without the registry nothing registers.
"""
try:
    from cis.menu_registry import menu
except ImportError:   # cis without the registry: the menu migrations still apply
    menu = None

if menu is not None:
    menu.register('ce', 'docrepo', 'Documents', url='docrepo:all',
                  icon='fas fa-fw fa-folder', order=130)
    menu.register('faculty', 'docrepo', 'Documents Library',
                  url='faculty_docrepo:docs', icon='fas fa-fw fa-folder', order=70)
    menu.register('instructor', 'docrepo', 'Shared Docs.',
                  url='instructor_docrepo:docs', icon='fas fa-fw fa-folder', order=80)

# The student and HS admin Documents items are registered hidden by the
# @menu.item decorators on their views; importing the module runs them.
from .views import views as _views  # noqa: E402,F401
