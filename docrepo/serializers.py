from django.contrib.auth import get_user_model

from rest_framework import serializers

from cis.serializers.highschool_admin import CustomUserSerializer

from .models.model import DocRepo

class DocRepoSerializer(serializers.ModelSerializer):
    uploaded_by = CustomUserSerializer()
    uploaded_on = serializers.DateTimeField(
        format='%m/%d/%Y',
        read_only=True
    )
    ce_url = serializers.CharField(
        read_only=True
    )

    class Meta:
        model = DocRepo
        fields = '__all__'

        datatables_always_serialize = [
            'id',
            'ce_url'
        ]
