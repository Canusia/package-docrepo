MyCE - Document Repository
==========================

Shared document library for the MyCE platform. CE staff upload files into
private S3 storage and tag which portal roles (Students / High School
Administrators / Instructors / Faculty) may see them; each role portal renders
a read-only download list.

Install
-------

::

    git+https://github.com/Canusia/package-docrepo.git@v0.0.1

Add to ``INSTALLED_APPS``::

    'docrepo.docrepo.apps.DevDocRepoConfig'
    if importlib.util.find_spec('docrepo.docrepo')
    else 'docrepo.apps.DocRepoConfig',

Mount the URLs (``_dr`` resolves to ``docrepo.docrepo`` or ``docrepo``)::

    path('ce/documents/',         include(f'{_dr}.urls.ce')),
    path('instructor/documents/', include(f'{_dr}.urls.instructor')),
    path('student/documents/',    include(f'{_dr}.urls.student')),
    path('faculty/documents/',    include(f'{_dr}.urls.faculty')),
