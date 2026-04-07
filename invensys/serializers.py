from rest_framework import serializers
from .models import Category, Unit


class Metadata:
    read_only_fields = ['id', 'created_at', 'created_by', 'updated_at', 'updated_by']


class CategorySerializer(serializers.ModelSerializer):
    class Meta(Metadata):
        model = Category
        fields = ['name'] + Metadata.read_only_fields


class UnitSerializer(serializers.ModelSerializer):
    class Meta(Metadata):
        model = Unit
        fields = ['name'] + Metadata.read_only_fields
