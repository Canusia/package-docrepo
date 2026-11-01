from django.apps import AppConfig


class DocRepoConfig(AppConfig):
    """Production config — package installed 1-deep via pip (``docrepo``)."""
    name = 'docrepo'

    def ready(self):
        from . import menu  # noqa: F401  sidebar items (cis.menu_registry)


class DevDocRepoConfig(AppConfig):
    """Dev config — editable submodule, 2-deep (``docrepo.docrepo``)."""
    name = 'docrepo.docrepo'

    def ready(self):
        from . import menu  # noqa: F401  sidebar items (cis.menu_registry)
