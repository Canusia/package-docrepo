from django import forms
from django.forms.widgets import Input

from ..models.model import DocRepo


class DropzoneFileInput(Input):
    """A file input that file_dropzone.js turns into a drag-and-drop zone.

    It posts like ``forms.FileInput`` but deliberately isn't a subclass:
    crispy wraps every FileInput in Bootstrap's ``custom-file`` markup (a fixed
    height, a "---" label and an inline onchange that breaks once the drop zone
    moves the input), so this one renders as a plain field instead.
    """
    input_type = 'file'
    needs_multipart_form = True
    template_name = 'django/forms/widgets/file.html'

    def format_value(self, value):
        return None   # a browser never pre-fills a file input

    def value_from_datadict(self, data, files, name):
        return files.get(name)

    def value_omitted_from_data(self, data, files, name):
        return name not in files

    def use_required_attribute(self, initial):
        return super().use_required_attribute(initial) and not initial


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
        # The field is called "media", so in a template {{ form.media }} renders
        # the file field (dict lookup wins), not the form's JS/CSS. Views pass
        # form.media as form_assets instead.
        widgets = {
            'media': DropzoneFileInput(attrs={
                'data-dropzone': '',
                'data-dropzone-prompt': 'Drag the document here',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance._state.adding:   # the document page (pk is a default UUID, so never None)
            self.fields['media'].widget.attrs['data-dropzone-prompt'] = (
                'Drag a replacement file here')
