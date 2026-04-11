from datetime import date
from decimal import Decimal
from django.test import TestCase
from ...models import (
    Category, Customer, Product, PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem,
    Supplier, Unit
)
from ...serializers import PurchaseOrderDetailSerializer, SalesOrderDetailSerializer


class SalesOrderDetailSerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Cat')
        self.unit = Unit.objects.create(name='pcs')
        self.unit2 = Unit.objects.create(name='box')
        self.product = Product.objects.create(name='A', category=self.category)
        self.product2 = Product.objects.create(name='B', category=self.category)
        self.customer = Customer.objects.create(name='Buyer')

    def test_create_sales_order_with_items(self):
        data = {
            'customer_id': self.customer.pk,
            'delivery_date': str(date(2026, 6, 1)),
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 2,
                    'price': '12.50',
                    'unit_id': self.unit.pk,
                },
            ],
        }
        serializer = SalesOrderDetailSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        order = serializer.save()

        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.items.count(), 1)
        item = order.items.get()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.unit, self.unit)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal('12.50'))

    def test_update_create_new_items_update_existing_delete_missing(self):
        order = SalesOrder.objects.create(customer=self.customer)
        item1 = SalesOrderItem.objects.create(
            sales=order,
            product=self.product,
            unit=self.unit,
            quantity=1,
            price=Decimal('3.00'),
        )
        item2 = SalesOrderItem.objects.create(
            sales=order,
            product=self.product2,
            unit=self.unit2,
            quantity=2,
            price=Decimal('4.00'),
        )

        data = {
            'customer_id': self.customer.pk,
            'delivery_date': str(date(2026, 7, 1)),
            'items': [
                {
                    'id': item1.pk,
                    'product_id': self.product2.pk,
                    'quantity': 5,
                    'price': Decimal('9.00'),
                    'unit_id': self.unit2.pk,
                },
                {
                    'product_id': self.product.pk,
                    'quantity': 1,
                    'price': Decimal('1.00'),
                    'unit_id': self.unit.pk,
                },
            ],
        }
        serializer = SalesOrderDetailSerializer(instance=order, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertFalse(SalesOrderItem.objects.filter(pk=item2.pk).exists())
        self.assertEqual(order.items.count(), 2)

        self.assertEqual(order.items.get(pk=item1.pk).product, self.product2)
        self.assertEqual(order.items.get(pk=item1.pk).quantity, 5)
        self.assertTrue(
            order.items.filter(product=self.product, quantity=1, price=Decimal('1.00')).exists()
        )


class PurchaseOrderDetailSerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Cat')
        self.unit = Unit.objects.create(name='pcs')
        self.unit2 = Unit.objects.create(name='box')
        self.product = Product.objects.create(name='A', category=self.category)
        self.product2 = Product.objects.create(name='B', category=self.category)
        self.supplier = Supplier.objects.create(name='Vendor')

    def test_create_purchase_order_with_items(self):
        data = {
            'supplier_id': self.supplier.pk,
            'arrival_date': str(date(2026, 6, 1)),
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 2,
                    'price': '12.50',
                    'unit_id': self.unit.pk,
                },
            ],
        }
        serializer = PurchaseOrderDetailSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        order = serializer.save()

        self.assertEqual(order.supplier, self.supplier)
        self.assertEqual(order.items.count(), 1)
        item = order.items.get()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.unit, self.unit)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal('12.50'))

    def test_update_create_new_items_update_existing_delete_missing(self):
        order = PurchaseOrder.objects.create(supplier=self.supplier)
        item1 = PurchaseOrderItem.objects.create(
            purchase=order,
            product=self.product,
            unit=self.unit,
            quantity=1,
            price=Decimal('3.00'),
        )
        item2 = PurchaseOrderItem.objects.create(
            purchase=order,
            product=self.product2,
            unit=self.unit2,
            quantity=2,
            price=Decimal('4.00'),
        )

        data = {
            'supplier_id': self.supplier.pk,
            'arrival_date': str(date(2026, 8, 1)),
            'items': [
                {
                    'id': item1.pk,
                    'product_id': self.product2.pk,
                    'quantity': 5,
                    'price': Decimal('9.00'),
                    'unit_id': self.unit2.pk,
                },
                {
                    'product_id': self.product.pk,
                    'quantity': 1,
                    'price': Decimal('1.00'),
                    'unit_id': self.unit.pk,
                },
            ],
        }
        serializer = PurchaseOrderDetailSerializer(instance=order, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertFalse(PurchaseOrderItem.objects.filter(pk=item2.pk).exists())
        self.assertEqual(order.items.count(), 2)

        self.assertEqual(order.items.get(pk=item1.pk).product, self.product2)
        self.assertEqual(order.items.get(pk=item1.pk).quantity, 5)
        self.assertTrue(
            order.items.filter(product=self.product, quantity=1, price=Decimal('1.00')).exists()
        )
