"""
    Student URL Configuration
"""
from django.urls import path

from ..views.views import (
    show_links_for_highschool_admin
)

app_name = 'highschool_admin_docrepo'
urlpatterns = [
    path('', show_links_for_highschool_admin, name='docs'),
]
