from django.test import TestCase
from invensys.models import Category
from django.db import IntegrityError


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')

    def test_slug_is_generated_from_name(self):
        self.assertEqual(self.category.slug, 'test-category')

    def test_update_slug_when_name_is_changed(self):
        self.assertEqual(self.category.slug, 'test-category')
        self.category.name = 'Updated Category'
        self.category.save()
        self.assertEqual(self.category.slug, 'updated-category')

    def test_slug_is_unique(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Test Category')

    def test_slug_remove_special_characters(self):
        category = Category.objects.create(name='Test! & Category @#$%^&*() End')
        self.assertEqual(category.slug, 'test-category-end')

    def test_string_representation(self):
        self.assertEqual(str(self.category), 'Test Category')
