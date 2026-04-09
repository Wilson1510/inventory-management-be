from rest_framework import serializers
from ..models import Category
from ..constants import METADATA_FIELDS, READ_ONLY_FIELDS


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name'] + METADATA_FIELDS
        read_only_fields = READ_ONLY_FIELDS


class CategoryNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
