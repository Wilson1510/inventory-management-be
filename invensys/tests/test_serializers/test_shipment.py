from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from ...models import (
    Category, Customer, Delivery, DeliveryItem, Product, PurchaseOrder, Receipt, ReceiptItem,
    SalesOrder, Supplier, Unit,
)
from ...serializers import DeliveryDetailSerializer, ReceiptDetailSerializer


class DeliverySerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Cat')
        self.unit = Unit.objects.create(name='pcs')
        self.product = Product.objects.create(name='A', category=self.category)
        self.product2 = Product.objects.create(name='B', category=self.category)
        self.customer = Customer.objects.create(
            name='Buyer',
            address='123 Business Rd',
        )
        self.sales_order = SalesOrder.objects.create(customer=self.customer)
        self.delivery = Delivery.objects.create(
            sales_order=self.sales_order,
            delivery_date=date.today() + timedelta(days=1),
        )
        self.d_item = DeliveryItem.objects.create(
            delivery=self.delivery,
            product=self.product,
            unit=self.unit,
            quantity=10,
            quantity_delivered=0,
        )
        self.d_item2 = DeliveryItem.objects.create(
            delivery=self.delivery,
            product=self.product2,
            unit=self.unit,
            quantity=20,
            quantity_delivered=0,
        )

    def test_detail_destination_is_customer_address(self):
        data = DeliveryDetailSerializer(self.delivery).data
        self.assertEqual(data['destination'], '123 Business Rd')

    def test_detail_destination_none_when_customer_has_no_address(self):
        self.customer.address = None
        self.customer.save()
        data = DeliveryDetailSerializer(self.delivery).data
        self.assertIsNone(data['destination'])

    def test_update_notes_method_and_line_items(self):
        data = {
            'notes': 'Handle with care',
            'method': Delivery.ShipmentMethod.DELIVERY,
            'items': [
                {'id': self.d_item.pk, 'quantity_delivered': 10, 'notes': 'Line one'},
                {'id': self.d_item2.pk, 'quantity_delivered': 5, 'notes': 'Line two'},
            ]
        }
        serializer = DeliveryDetailSerializer(instance=self.delivery, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.notes, 'Handle with care')
        self.assertEqual(self.delivery.method, Delivery.ShipmentMethod.DELIVERY)

        self.d_item.refresh_from_db()
        self.d_item2.refresh_from_db()
        self.assertEqual(self.d_item.quantity_delivered, 10)
        self.assertEqual(self.d_item.notes, 'Line one')
        self.assertEqual(self.d_item2.quantity_delivered, 5)
        self.assertEqual(self.d_item2.notes, 'Line two')

    def test_update_notes_only_leaves_items_unchanged(self):
        data = {'notes': 'Only notes'}
        serializer = DeliveryDetailSerializer(instance=self.delivery, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.d_item.refresh_from_db()
        self.assertEqual(self.d_item.quantity_delivered, 0)

    def test_rejects_quantity_delivered_greater_than_quantity(self):
        data = {
            'items': [
                {'id': self.d_item.pk, 'quantity_delivered': 11},
            ]
        }
        serializer = DeliveryDetailSerializer(instance=self.delivery, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)

    def test_rejects_invalid_item_id(self):
        data = {
            'items': [
                {'id': 99999, 'quantity_delivered': 1},
            ]
        }
        serializer = DeliveryDetailSerializer(instance=self.delivery, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)

    def test_rejects_item_row_missing_id(self):
        data = {
            'items': [
                {'quantity_delivered': 1},
            ]
        }
        serializer = DeliveryDetailSerializer(instance=self.delivery, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)


class ReceiptSerializerTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Cat')
        self.unit = Unit.objects.create(name='pcs')
        self.product = Product.objects.create(name='A', category=self.category)
        self.product2 = Product.objects.create(name='B', category=self.category)
        self.supplier = Supplier.objects.create(
            name='Vendor',
            address='Warehouse Way 9',
        )
        self.purchase_order = PurchaseOrder.objects.create(supplier=self.supplier)
        self.receipt = Receipt.objects.create(
            purchase_order=self.purchase_order,
            arrival_date=date.today() + timedelta(days=1),
        )
        self.r_item = ReceiptItem.objects.create(
            receipt=self.receipt,
            product=self.product,
            unit=self.unit,
            quantity=10,
            quantity_received=0,
            price=Decimal('12.00'),
        )
        self.r_item2 = ReceiptItem.objects.create(
            receipt=self.receipt,
            product=self.product2,
            unit=self.unit,
            quantity=20,
            quantity_received=0,
            price=Decimal('8.00'),
        )

    def test_detail_destination_is_supplier_address(self):
        data = ReceiptDetailSerializer(self.receipt).data
        self.assertEqual(data['destination'], 'Warehouse Way 9')

    def test_detail_destination_none_when_supplier_has_no_address(self):
        self.supplier.address = None
        self.supplier.save()
        data = ReceiptDetailSerializer(self.receipt).data
        self.assertIsNone(data['destination'])

    def test_update_notes_method_and_line_items(self):
        data = {
            'notes': 'Unload at dock B',
            'method': Receipt.ShipmentMethod.PICKUP,
            'items': [
                {'id': self.r_item.pk, 'quantity_received': 10, 'notes': 'OK'},
                {'id': self.r_item2.pk, 'quantity_received': 4, 'notes': 'Partial'},
            ]
        }
        serializer = ReceiptDetailSerializer(instance=self.receipt, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.notes, 'Unload at dock B')
        self.assertEqual(self.receipt.method, Receipt.ShipmentMethod.PICKUP)

        self.r_item.refresh_from_db()
        self.r_item2.refresh_from_db()
        self.assertEqual(self.r_item.quantity_received, 10)
        self.assertEqual(self.r_item2.quantity_received, 4)

    def test_update_notes_only_leaves_items_unchanged(self):
        data = {'notes': 'Only notes'}
        serializer = ReceiptDetailSerializer(instance=self.receipt, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.r_item.refresh_from_db()
        self.assertEqual(self.r_item.quantity_received, 0)

    def test_rejects_quantity_received_greater_than_quantity(self):
        data = {
            'items': [
                {'id': self.r_item.pk, 'quantity_received': 11},
            ]
        }
        serializer = ReceiptDetailSerializer(instance=self.receipt, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)

    def test_rejects_invalid_item_id(self):
        data = {
            'items': [
                {'id': 88888, 'quantity_received': 1},
            ]
        }
        serializer = ReceiptDetailSerializer(instance=self.receipt, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)

    def test_rejects_item_row_missing_id(self):
        data = {
            'items': [
                {'quantity_received': 1},
            ]
        }
        serializer = ReceiptDetailSerializer(instance=self.receipt, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('items', serializer.errors)
