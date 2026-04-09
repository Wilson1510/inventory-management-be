from decimal import Decimal
from django.test import TestCase
from ...models import Category, Product, ProductPrice, ProductUnit, Unit
from ...serializers import (
    ProductDetailSerializer,
    ProductListSerializer,
    ProductPriceSerializer,
    ProductUnitSerializer,
)


class ProductPriceSerializerTest(TestCase):
    def setUp(self):
        self.unit = Unit.objects.create(name='pcs')

    def test_to_representation(self):
        category = Category.objects.create(name='Cat')
        product = Product.objects.create(name='Product', category=category)
        product_price = ProductPrice.objects.create(
            product=product,
            unit=self.unit,
            price=Decimal('12.50'),
            minimum_quantity=1,
        )
        data = ProductPriceSerializer(product_price).data
        self.assertIn('unit', data)
        self.assertEqual(data['unit']['id'], self.unit.pk)
        self.assertNotIn('unit_id', data)


class ProductUnitSerializerTest(TestCase):
    def setUp(self):
        self.unit = Unit.objects.create(name='pcs')

    def test_to_representation(self):
        category = Category.objects.create(name='Cat')
        product = Product.objects.create(name='Product', category=category)
        product_unit = ProductUnit.objects.create(
            product=product,
            unit=self.unit
        )
        data = ProductUnitSerializer(product_unit).data
        self.assertIn('unit', data)
        self.assertEqual(data['unit']['id'], self.unit.pk)
        self.assertNotIn('unit_id', data)


class ProductDetailSerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Cat')
        self.unit = Unit.objects.create(name='pcs')

    def test_create_product_with_prices_and_units(self):
        data = {
            'name': 'Widget',
            'category_id': self.category.pk,
            'prices': [
                {'price': '12.50', 'minimum_quantity': 1, 'unit_id': self.unit.pk},
            ],
            'units': [
                {'unit_id': self.unit.pk, 'multiplier': 1, 'is_base_unit': True},
            ],
        }
        serializer = ProductDetailSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        product = serializer.save()

        self.assertEqual(product.name, 'Widget')
        self.assertEqual(product.prices.count(), 1)
        self.assertEqual(product.productunit_set.count(), 1)

        price = product.prices.get()
        self.assertEqual(price.price, Decimal('12.50'))
        self.assertEqual(price.unit, self.unit)

        unit = product.productunit_set.get()
        self.assertEqual(unit.unit, self.unit)
        self.assertEqual(unit.multiplier, 1)
        self.assertEqual(unit.is_base_unit, True)

    def test_update_create_new_children_update_existing_children_delete_missing_children(self):
        product = Product.objects.create(name='Y', category=self.category)
        unit2 = Unit.objects.create(name='pcs2')
        pu1 = ProductUnit.objects.create(
            product=product, unit=self.unit, multiplier=1, is_base_unit=True
        )
        pu2 = ProductUnit.objects.create(
            product=product, unit=unit2, multiplier=2, is_base_unit=False
        )
        pp1 = ProductPrice.objects.create(
            product=product, unit=self.unit, price=Decimal('3.00'), minimum_quantity=1
        )
        pp2 = ProductPrice.objects.create(
            product=product, unit=self.unit, price=Decimal('4.00'), minimum_quantity=2
        )

        data = {
            'name': 'Y Updated',
            'category_id': self.category.pk,
            'prices': [
                {'id': pp1.pk, 'price': Decimal('9.00'), 'unit_id': self.unit.pk},
                {'price': Decimal('4.00'), 'minimum_quantity': 2, 'unit_id': self.unit.pk},
            ],
            'units': [
                {'id': pu1.pk, 'unit_id': unit2.pk, 'multiplier': 1, 'is_base_unit': True},
                {'unit_id': self.unit.pk, 'multiplier': 2, 'is_base_unit': False},
            ],
        }
        serializer = ProductDetailSerializer(instance=product, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertFalse(ProductPrice.objects.filter(pk=pp2.pk).exists())
        self.assertFalse(ProductUnit.objects.filter(pk=pu2.pk).exists())

        self.assertEqual(product.prices.count(), 2)
        self.assertEqual(product.productunit_set.count(), 2)

        self.assertEqual(product.prices.get(pk=pp1.pk).price, Decimal('9.00'))
        self.assertTrue(product.prices.filter(unit=self.unit, minimum_quantity=2).exists())

        self.assertEqual(product.productunit_set.get(pk=pu1.pk).unit, unit2)
        self.assertTrue(product.productunit_set.filter(unit=self.unit, multiplier=2).exists())


class ProductListSerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Cat')
        self.unit1 = Unit.objects.create(name='pcs1')
        self.unit2 = Unit.objects.create(name='pcs2')

    def test_price_and_unit_from_base_unit_and_matching_price(self):
        product = Product.objects.create(name='B', category=self.category)
        ProductUnit.objects.create(
            product=product, unit=self.unit1, multiplier=1, is_base_unit=True
        )
        ProductUnit.objects.create(
            product=product, unit=self.unit2, multiplier=2, is_base_unit=False
        )
        ProductPrice.objects.create(
            product=product, unit=self.unit1, price=Decimal('99.00'), minimum_quantity=1
        )
        ProductPrice.objects.create(
            product=product, unit=self.unit2, price=Decimal('199.00'), minimum_quantity=2
        )

        data = ProductListSerializer(instance=product).data
        self.assertEqual(data['unit'], 'pcs1')
        self.assertEqual(Decimal(str(data['price'])), Decimal('99.00'))

    def test_price_and_unit_none_without_base_or_price(self):
        product = Product.objects.create(name='C', category=self.category)
        ProductUnit.objects.create(
            product=product, unit=self.unit1, multiplier=12, is_base_unit=False
        )

        data = ProductListSerializer(instance=product).data
        self.assertIsNone(data['unit'])
        self.assertIsNone(data['price'])
