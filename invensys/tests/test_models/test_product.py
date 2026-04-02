from django.test import TestCase
from invensys.models import Category, Product, Unit
from django.db import IntegrityError


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category
        )
        self.unit = Unit.objects.create(name='Test Unit')

    def test_slug_is_generated_from_name_when_slug_is_not_set(self):
        self.assertEqual(self.product.slug, 'test-product')

    def test_slug_is_not_changed_when_name_is_changed(self):
        self.assertEqual(self.product.slug, 'test-product')
        self.product.name = 'Updated Product'
        self.product.save()
        self.assertEqual(self.product.slug, 'test-product')

    def test_slug_is_not_set_from_name_when_slug_is_set(self):
        product = Product.objects.create(
            name='Test Product',
            category=self.category,
            slug='test-product-slug'
        )
        self.assertEqual(product.slug, 'test-product-slug')

    def test_slug_is_unique(self):
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name='Test Product',
                category=self.category
            )

    def test_slug_remove_special_characters(self):
        product = Product.objects.create(
            name='Test! & Product @#$%^&*() End',
            category=self.category
        )
        self.assertEqual(product.slug, 'test-product-end')

    def test_sku_number_is_unique(self):
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name='Test Product 2',
                category=self.category,
                sku_number=self.product.sku_number
            )

    def test_base_price_is_set_to_0_by_default(self):
        self.assertEqual(self.product.base_price, 0)

    def test_quantity_is_set_to_0_by_default(self):
        self.assertEqual(self.product.quantity, 0)

    def test_string_representation(self):
        self.assertEqual(str(self.product), 'Test Product')
