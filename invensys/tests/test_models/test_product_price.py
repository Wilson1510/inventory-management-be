from django.test import TestCase
from invensys.models import Product, Unit, ProductPrice, Category
from django.db import IntegrityError


class ProductPriceModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product', category=self.category, sku_number='1234567890'
        )
        self.unit = Unit.objects.create(name='Test Unit')
        self.product_price = ProductPrice.objects.create(
            product=self.product, unit=self.unit, price=100
        )

    def test_product_price_minimum_quantity_is_set_to_1_by_default(self):
        self.assertEqual(self.product_price.minimum_quantity, 1)

    def test_product_price_is_unique(self):
        with self.assertRaises(IntegrityError):
            ProductPrice.objects.create(product=self.product, unit=self.unit)

    def test_string_representation(self):
        self.assertEqual(str(self.product_price), 'Test Product - 100')
