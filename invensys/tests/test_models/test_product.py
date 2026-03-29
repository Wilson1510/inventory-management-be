from django.test import TestCase
from invensys.models import Category, Product, Unit
from django.db import IntegrityError


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            sku_number='1234567890'
        )
        self.unit = Unit.objects.create(name='Test Unit')

    def test_slug_is_generated_from_name(self):
        self.assertEqual(self.product.slug, 'test-product')

    def test_update_slug_when_name_is_changed(self):
        self.assertEqual(self.product.slug, 'test-product')
        self.product.name = 'Updated Product'
        self.product.save()
        self.assertEqual(self.product.slug, 'updated-product')

    def test_slug_is_unique(self):
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name='Test Product',
                category=self.category,
                sku_number='1234567891'
            )

    def test_slug_remove_special_characters(self):
        product = Product.objects.create(
            name='Test! & Product @#$%^&*() End',
            category=self.category,
            sku_number='1234567892'
        )
        self.assertEqual(product.slug, 'test-product-end')

    def test_sku_number_is_unique(self):
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name='Test Product 2',
                category=self.category,
                sku_number='1234567890'
            )

    def test_base_price_is_set_to_0_by_default(self):
        self.assertEqual(self.product.base_price, 0)

    def test_quantity_is_set_to_0_by_default(self):
        self.assertEqual(self.product.quantity, 0)

    def test_string_representation(self):
        self.assertEqual(str(self.product), 'Test Product')
