from django import forms

from cis.models.customuser import CustomUser

from ..models.model import DocRepo

class DocRepoForm(forms.ModelForm):

    class Meta:
        model = DocRepo
        fields = [
            'title',
            'media',
            'description',
            'available_to',
            'display_weight',
            ]
        labels = {
            'description': 'Description',
            'media': 'File'
        }
