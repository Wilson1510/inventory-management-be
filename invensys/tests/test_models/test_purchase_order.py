from django.test import TestCase
from invensys.models import (
    PurchaseOrder, PurchaseOrderItem, Product, Supplier, Category, Unit, ProductUnit, Receipt
)
from django.utils import timezone
from datetime import timedelta


class BasePurchaseOrderTest(TestCase):
    def setUp(self):
        self.units = Unit.objects.bulk_create([
            Unit(name='Test Unit 1'),
            Unit(name='Test Unit 2'),
            Unit(name='Test Unit 3'),
        ])
        self.categories = Category.objects.create(name='Test Category')
        self.products = [
            Product.objects.create(name='Test Product 1', category=self.categories),
            Product.objects.create(name='Test Product 2', category=self.categories),
            Product.objects.create(name='Test Product 3', category=self.categories),
        ]
        ProductUnit.objects.bulk_create([
            ProductUnit(product=self.products[0], unit=self.units[0], is_base_unit=True),
            ProductUnit(product=self.products[1], unit=self.units[1], is_base_unit=True),
            ProductUnit(product=self.products[2], unit=self.units[2], is_base_unit=True),
        ])
        ProductUnit.objects.bulk_create([
            ProductUnit(product=self.products[0], unit=self.units[1], multiplier=2),
            ProductUnit(product=self.products[1], unit=self.units[2], multiplier=3),
            ProductUnit(product=self.products[2], unit=self.units[0], multiplier=4),
        ])
        self.supplier = Supplier.objects.create(name='Test Supplier')
        self.purchase_order = PurchaseOrder.objects.create(supplier=self.supplier)
        self.purchase_order_items = [
            PurchaseOrderItem.objects.create(
                purchase=self.purchase_order,
                product=self.products[0],
                price=100,
            ),
            PurchaseOrderItem.objects.create(
                purchase=self.purchase_order,
                product=self.products[1],
                quantity=2,
                price=200,
            ),
            PurchaseOrderItem.objects.create(
                purchase=self.purchase_order,
                product=self.products[2],
                quantity=3,
                price=300,
                unit=self.units[0],
            ),
        ]

    def fill_arrival_date(self):
        arrival_date = timezone.now().date() + timedelta(days=1)
        self.purchase_order.arrival_date = arrival_date
        self.purchase_order.save()


class PurchaseOrderModelTest(BasePurchaseOrderTest):
    def test_number_is_generated_when_order_is_created(self):
        self.assertEqual(self.purchase_order.number, f"PO{self.purchase_order.pk:05d}")

    def test_status_is_set_to_draft_by_default(self):
        self.assertEqual(self.purchase_order.status, PurchaseOrder.Status.DRAFT)

    def test_total_is_0_by_default(self):
        po = PurchaseOrder.objects.create(supplier=self.supplier)
        self.assertEqual(po.total, 0)

    def test_total_is_calculated_when_order_item_is_saved(self):
        self.assertEqual(self.purchase_order.total, 1400)
        self.purchase_order_items[0].quantity += 1
        self.purchase_order_items[0].save()
        self.assertEqual(self.purchase_order.total, 1500)

    def test_total_is_calculated_when_order_item_is_deleted(self):
        self.assertEqual(self.purchase_order.total, 1400)
        self.purchase_order_items[0].delete()
        self.assertEqual(self.purchase_order.total, 1300)

    def test_order_item_unit_is_set_to_base_unit_if_not_set(self):
        self.assertEqual(self.purchase_order_items[0].unit, self.units[0])
        self.assertEqual(self.purchase_order_items[1].unit, self.units[1])

    def test_order_item_unit_is_set_to_other_unit_if_set(self):
        self.assertEqual(self.purchase_order_items[2].unit, self.units[0])

    def test_cannot_confirm_order_with_no_items(self):
        po = PurchaseOrder.objects.create(supplier=self.supplier)
        with self.assertRaises(ValueError):
            po.confirm()

    def test_cannot_confirm_order_with_zero_quantity(self):
        po = PurchaseOrder.objects.create(supplier=self.supplier)
        PurchaseOrderItem.objects.create(
            purchase=po, product=self.products[0], quantity=0, price=100
        )
        with self.assertRaises(ValueError):
            po.confirm()

    def test_cannot_confirm_order_with_negative_quantity(self):
        po = PurchaseOrder.objects.create(supplier=self.supplier)
        PurchaseOrderItem.objects.create(
            purchase=po, product=self.products[0], quantity=-1, price=100
        )
        with self.assertRaises(ValueError):
            po.confirm()

    def test_cannot_confirm_order_with_arrival_date_in_the_past(self):
        arrival_date = timezone.now().date() - timedelta(days=1)
        self.purchase_order.arrival_date = arrival_date
        self.purchase_order.save()
        with self.assertRaises(ValueError):
            self.purchase_order.confirm()

    def test_cannot_confirm_order_with_arrival_date_not_set(self):
        with self.assertRaises(ValueError):
            self.purchase_order.confirm()

    def test_rollback_status_when_confirming_order_fails(self):
        self.fill_arrival_date()

        def error_method():
            raise ValueError("Test error")

        self.purchase_order._create_receipt_order_and_items = error_method
        with self.assertRaises(ValueError):
            self.purchase_order.confirm()
        self.purchase_order.refresh_from_db()

        self.assertEqual(self.purchase_order.status, PurchaseOrder.Status.DRAFT)
        self.assertEqual(self.purchase_order.receipts.count(), 0)

    def test_status_is_confirmed_when_order_is_confirmed(self):
        self.fill_arrival_date()
        self.purchase_order.confirm()
        self.assertEqual(self.purchase_order.status, PurchaseOrder.Status.CONFIRMED)

    def test_receipt_order_is_created_when_order_is_confirmed(self):
        self.fill_arrival_date()
        self.purchase_order.confirm()

        receipt_created = self.purchase_order.receipts
        self.assertEqual(receipt_created.count(), 1)
        self.assertEqual(receipt_created.first().arrival_date, self.purchase_order.arrival_date)
        self.assertEqual(receipt_created.first().status, Receipt.Status.DRAFT)
        self.assertEqual(receipt_created.first().purchase_order, self.purchase_order)

    def test_receipt_items_are_created_and_same_as_order_items_when_order_is_confirmed(self):
        self.fill_arrival_date()
        self.purchase_order.confirm()

        receipt_created = self.purchase_order.receipts
        self.assertEqual(receipt_created.first().items.count(), 3)
        self.assertEqual(receipt_created.first().items.first().product, self.products[0])
        self.assertEqual(receipt_created.first().items.first().quantity, 1)
        self.assertEqual(receipt_created.first().items.first().price, 100)
        self.assertEqual(receipt_created.first().items.first().unit, self.units[0])

    def test_status_is_cancelled_when_order_is_cancelled(self):
        self.purchase_order.cancel()
        self.assertEqual(self.purchase_order.status, PurchaseOrder.Status.CANCELLED)

    def test_receipts_are_cancelled_when_order_is_cancelled(self):
        self.fill_arrival_date()
        self.purchase_order.confirm()
        self.purchase_order.cancel()
        receipts = self.purchase_order.receipts
        for receipt in receipts.all():
            self.assertEqual(receipt.status, Receipt.Status.CANCELLED)

    def test_cannot_cancel_order_with_done_receipts(self):
        self.fill_arrival_date()
        self.purchase_order.confirm()
        receipts = self.purchase_order.receipts

        for item in receipts.first().items.all():
            item.quantity_received = item.quantity
            item.save()

        self.purchase_order.receipts.first().done()
        with self.assertRaises(ValueError):
            self.purchase_order.cancel()

    def test_po_str_returns_number(self):
        self.assertEqual(str(self.purchase_order), self.purchase_order.number)

    def test_po_item_str_returns_purchase_order_number_and_product_name(self):
        self.assertEqual(
            str(self.purchase_order_items[0]),
            f"{self.purchase_order.number} - {self.products[0].name}"
        )
        self.assertEqual(
            str(self.purchase_order_items[1]),
            f"{self.purchase_order.number} - {self.products[1].name}"
        )
        self.assertEqual(
            str(self.purchase_order_items[2]),
            f"{self.purchase_order.number} - {self.products[2].name}"
        )

    def test_cannot_delete_order_if_status_is_confirmed(self):
        self.fill_arrival_date()
        self.purchase_order.confirm()
        with self.assertRaises(ValueError):
            self.purchase_order.delete()

    def test_can_delete_order_if_status_is_not_confirmed(self):
        self.purchase_order.delete()
        self.assertEqual(PurchaseOrder.objects.count(), 0)
