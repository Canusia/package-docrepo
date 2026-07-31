"""
    Faculty URL Configuration
"""
from django.urls import path

from ..views.views import (
    show_links_for_faculty
)

app_name = 'faculty_docrepo'
urlpatterns = [
    path('', show_links_for_faculty, name='docs'),
]
