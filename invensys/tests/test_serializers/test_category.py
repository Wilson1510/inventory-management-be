from django.test import TestCase
from ...models import Category
from ...serializers import CategorySerializer, Metadata
from django.contrib.auth.models import User


class CategorySerializerTest(TestCase):
    def setUp(self):
        self.category_data = {'name': 'Test Category'}
        self.category = Category.objects.create(**self.category_data)
        self.user = User.objects.create(username='testuser')

    def test_metadata_is_read_only(self):
        metadata = {
            'id': 1,
            'created_at': '2026-04-03T00:00:00Z',
            'created_by': self.user,
            'updated_at': '2026-04-03T00:00:00Z',
            'updated_by': self.user,
        }
        data = {**self.category_data, **metadata}
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())

        for field in Metadata.read_only_fields:
            self.assertNotIn(field, serializer.validated_data)

    def test_data_output(self):
        serializer = CategorySerializer(instance=self.category)
        serializer_keys = set(serializer.data.keys())
        expected_keys = set(['name']) | set(Metadata.read_only_fields)
        self.assertEqual(serializer_keys, expected_keys)
        self.assertEqual(serializer.data['name'], self.category.name)

    def test_data_input(self):
        serializer = CategorySerializer(data=self.category_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], self.category_data['name'])

    def test_name_must_not_be_blank(self):
        data = {**self.category_data, 'name': ''}
        serializer = CategorySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_name_must_not_be_null(self):
        data = {**self.category_data, 'name': None}
        serializer = CategorySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
