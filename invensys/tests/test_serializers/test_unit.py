from django.test import TestCase
from ...models import Unit
from ...serializers import UnitSerializer


class UnitSerializerTest(TestCase):    
    def setUp(self):
        self.unit_data = {'name': 'Test Unit'}
        self.unit = Unit.objects.create(name='Test Unit 2')

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
