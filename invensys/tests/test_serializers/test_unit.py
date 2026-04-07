from django.test import TestCase
from ...models import Unit
from ...serializers import UnitSerializer, Metadata
from django.contrib.auth import get_user_model


class UnitSerializerTest(TestCase):
    def setUp(self):
        self.unit_data = {'name': 'Test Unit'}
        self.unit = Unit.objects.create(name='Test Unit 2')
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
        data = {**self.unit_data, **metadata}
        serializer = UnitSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        for field in Metadata.read_only_fields:
            self.assertNotIn(field, serializer.validated_data)

    def test_data_output(self):
        serializer = UnitSerializer(instance=self.unit)
        serializer_keys = set(serializer.data.keys())
        expected_keys = set(['name']) | set(Metadata.read_only_fields)
        self.assertEqual(serializer_keys, expected_keys)
        self.assertEqual(serializer.data['name'], self.unit.name)

    def test_data_input(self):
        serializer = UnitSerializer(data=self.unit_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], self.unit_data['name'])

    def test_name_must_not_be_blank(self):
        data = {**self.unit_data, 'name': ''}
        serializer = UnitSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_name_must_not_be_null(self):
        data = {**self.unit_data, 'name': None}
        serializer = UnitSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
