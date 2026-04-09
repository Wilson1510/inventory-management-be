from django.test import TestCase
from ...models import Category
from ...serializers import CategorySerializer
from ...serializers.utils import METADATA_FIELDS, READ_ONLY_FIELDS
from django.contrib.auth import get_user_model


class MetadataTest(TestCase):
    def setUp(self):
        self.category_data = {'name': 'Test Category'}
        self.category = Category.objects.create(**self.category_data)
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='x')

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

        for field in READ_ONLY_FIELDS:
            self.assertNotIn(field, serializer.validated_data)

    def test_data_output(self):
        serializer = CategorySerializer(instance=self.category)
        serializer_keys = set(serializer.data.keys())
        expected_keys = set(['name']) | set(METADATA_FIELDS)
        self.assertEqual(serializer_keys, expected_keys)
        self.assertEqual(serializer.data['name'], self.category.name)

    def test_data_input(self):
        serializer = CategorySerializer(data=self.category_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], self.category_data['name'])
