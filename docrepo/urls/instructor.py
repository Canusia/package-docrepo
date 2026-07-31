"""
    Student URL Configuration
"""
from django.urls import path

from ..views.views import (
    show_links_for_instructor
)

app_name = 'instructor_docrepo'
urlpatterns = [
    path('', show_links_for_instructor, name='docs'),
]
