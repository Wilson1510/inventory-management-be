from django.test import TestCase
from ...models import Category
from ...serializers import CategorySerializer


class CategorySerializerTest(TestCase):
    def setUp(self):
        self.category_data = {'name': 'Test Category'}
        self.category = Category.objects.create(**self.category_data)

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
