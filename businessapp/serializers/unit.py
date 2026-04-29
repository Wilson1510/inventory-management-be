from rest_framework import serializers
from ..models import Unit
from .utils import METADATA_FIELDS, READ_ONLY_FIELDS


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['name'] + METADATA_FIELDS
        read_only_fields = READ_ONLY_FIELDS


class UnitNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name']
