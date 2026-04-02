from django.test import TestCase
from invensys.models import Product, Unit, ProductUnit, Category
from django.db import IntegrityError


class ProductUnitModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(name='Test Product', category=self.category)
        self.unit1 = Unit.objects.create(name='Test Unit 1')
        self.unit2 = Unit.objects.create(name='Test Unit 2')
        self.unit3 = Unit.objects.create(name='Test Unit 3')
        self.product_unit_base = ProductUnit.objects.create(
            product=self.product, unit=self.unit3, is_base_unit=True
        )
        self.product_unit_other1 = ProductUnit.objects.create(
            product=self.product, unit=self.unit1, multiplier=2
        )
        self.product_unit_other2 = ProductUnit.objects.create(
            product=self.product, unit=self.unit2, multiplier=3
        )

    def test_product_unit_multiplier_is_set_to_1_by_default(self):
        self.assertEqual(self.product_unit_base.multiplier, 1)
        self.assertEqual(self.product_unit_other1.multiplier, 2)
        self.assertEqual(self.product_unit_other2.multiplier, 3)

    def test_product_unit_is_base_unit_is_set_to_false_by_default(self):
        self.assertFalse(self.product_unit_other1.is_base_unit)
        self.assertFalse(self.product_unit_other2.is_base_unit)
        self.assertTrue(self.product_unit_base.is_base_unit)

    def test_product_unit_is_unique(self):
        with self.assertRaises(IntegrityError):
            ProductUnit.objects.create(
                product=self.product, unit=self.unit1, multiplier=2
            )

    def test_all_product_units_are_set_to_false_when_is_base_unit_is_set_to_true(self):
        self.product_unit_other1.is_base_unit = True
        self.product_unit_other1.save()

        self.product_unit_other1.refresh_from_db()
        self.product_unit_other2.refresh_from_db()
        self.product_unit_base.refresh_from_db()

        self.assertTrue(self.product_unit_other1.is_base_unit)
        self.assertFalse(self.product_unit_other2.is_base_unit)
        self.assertFalse(self.product_unit_base.is_base_unit)

    def test_string_representation(self):
        self.assertEqual(str(self.product_unit_base), 'Test Product - Test Unit 3')
        self.assertEqual(str(self.product_unit_other1), 'Test Product - Test Unit 1')
        self.assertEqual(str(self.product_unit_other2), 'Test Product - Test Unit 2')
