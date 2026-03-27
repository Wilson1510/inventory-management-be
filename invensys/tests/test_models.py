from django.test import TestCase
from invensys.models import Category


class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(name='Test Category')
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.slug, 'test-category')
