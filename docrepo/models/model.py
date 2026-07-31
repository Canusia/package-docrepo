# users/models.py
import os, uuid, datetime
from django.conf import settings
from django.urls import reverse_lazy

from django.contrib.auth import get_user_model
from django.db import models, IntegrityError
from django.dispatch import receiver

from multiselectfield import MultiSelectField
from tinymce.models import HTMLField

from cis.storage_backend import PrivateMediaStorage

def docrepo_upload_path(instance, filename):
    return f'docrepo/{instance.id}/{filename}'

class DocRepo(models.Model):
    """
    model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = HTMLField()

    STUDENTS = 'Students'
    SCHOOL_ADMINS = 'High School Administrators'

    APPLIES_TO = [
        (STUDENTS, STUDENTS),
        (SCHOOL_ADMINS, SCHOOL_ADMINS),
        ('Instructors', 'Instructors'),
        ('Faculty', 'Faculty'),
    ]

    available_to = MultiSelectField(
        max_length=300,
        choices=APPLIES_TO
    )

    display_weight = models.SmallIntegerField(default=0)
    
    media = models.FileField(
        storage=PrivateMediaStorage(),
        upload_to=docrepo_upload_path
    )
    uploaded_on = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey('cis.CustomUser', on_delete=models.PROTECT)

    def __str__(self):
        return self.title

    @property
    def ce_url(self):
        return reverse_lazy('docrepo:doc', kwargs={
            'record_id': self.id})