"""
    Student URL Configuration
"""
from django.urls import path

from ..views.views import (
    show_links_for_student
)

app_name = 'student_docrepo'
urlpatterns = [
    path('', show_links_for_student, name='docs'),
]
