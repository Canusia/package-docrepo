"""
    Important Link CE URL Configuration
"""
from django.urls import path, include
from rest_framework import routers

from ..views.views import (
    index, detail, add_new, delete,
    DocRepoViewSet
)

app_name = 'docrepo'

router = routers.DefaultRouter()
router.register('', DocRepoViewSet, basename='docrepo')

urlpatterns = [
    path('', index, name='all'),
    path('document/<uuid:record_id>', detail, name='doc'),
    path('document/add_new', add_new, name='add_new'),
    path('document/delete/<uuid:record_id>', delete, name='delete'),

    path('api/', include(router.urls)),
]
