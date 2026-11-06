"""Permanent document links, for every role (app_name 'docrepo_files').

Mounted by the host outside the role prefixes, e.g.
``path('documents/file/', include(f'{_dr}.urls.files'))``; the view checks
access itself.
"""
from django.urls import path

from ..views.views import open_file

app_name = 'docrepo_files'
urlpatterns = [
    path('<uuid:record_id>/', open_file, name='open'),
]
