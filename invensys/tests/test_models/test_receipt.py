from .test_purchase_order import BasePurchaseOrderTest
from invensys.models import Receipt, PurchaseOrder, PurchaseOrderItem
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class ReceiptModelTest(BasePurchaseOrderTest):
    def setUp(self):
        super().setUp()
        self.fill_arrival_date()
        self.purchase_order.confirm()
        self.receipt = self.purchase_order.receipts.first()

    def fill_quantity_received(self):
        for item in self.receipt.items.all():
            item.quantity_received = item.quantity
            item.save()

    def test_number_is_generated_when_receipt_is_created(self):
        self.assertEqual(self.receipt.number, f"RI{self.receipt.pk:05d}")

    def test_status_is_set_to_draft_by_default(self):
        self.assertEqual(self.receipt.status, Receipt.Status.DRAFT)

    def test_checked_at_and_checked_by_are_null_by_default(self):
        self.assertIsNone(self.receipt.checked_at)
        self.assertIsNone(self.receipt.checked_by)

    def test_status_is_set_to_done_when_receipt_is_done(self):
        self.fill_quantity_received()
        self.receipt.done()
        self.assertEqual(self.receipt.status, Receipt.Status.DONE)

    def test_checked_at_and_checked_by_are_set_when_receipt_is_done(self):
        self.fill_quantity_received()
        self.receipt.done()
        self.assertIsNotNone(self.receipt.checked_at)
        # TODO: Add the user who is logged in
        self.assertIsNone(self.receipt.checked_by)

    def test_product_quantity_is_added_when_receipt_is_done(self):
        self.fill_quantity_received()
        self.assertEqual(self.products[0].quantity, 0)
        self.receipt.done()
        self.products[0].refresh_from_db()
        self.assertEqual(self.products[0].quantity, 1)

    def test_product_base_price_is_adjusted_when_receipt_is_done(self):
        self.fill_quantity_received()
        self.assertEqual(self.products[0].base_price, 0)
        self.receipt.done()
        self.products[0].refresh_from_db()
        self.assertEqual(self.products[0].base_price, 100)

        new_po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            arrival_date=timezone.now().date() + timedelta(days=2)
        )
        PurchaseOrderItem.objects.create(
            purchase=new_po,
            product=self.products[0],
            quantity=3,
            price=150,
            unit=self.units[1],
        )
        new_po.confirm()
        new_receipt = new_po.receipts.first()
        for item in new_receipt.items.all():
            item.quantity_received = item.quantity
            item.save()
        new_receipt.done()
        self.products[0].refresh_from_db()
        # price=150 is per PO line unit (units[1]), not per base unit: line value = 3 * 150 = 450.
        # Weighted base_price = (1*100 + 450) / (1 + 6) = 550/7 → 78.57 after quantize.
        self.assertEqual(self.products[0].base_price, Decimal("78.57"))

    def test_status_is_set_to_cancelled_when_receipt_is_cancelled(self):
        self.receipt.cancel()
        self.assertEqual(self.receipt.status, Receipt.Status.CANCELLED)

    def test_receipt_item_get_multiplier_returns_multiplier(self):
        items = self.receipt.items.all()
        self.assertEqual(items[0].get_multiplier(), 1)
        self.assertEqual(items[1].get_multiplier(), 1)
        self.assertEqual(items[2].get_multiplier(), 4)

    def test_str_returns_number(self):
        self.assertEqual(str(self.receipt), self.receipt.number)

    def test_receipt_item_str_returns_receipt_number_and_product_name(self):
        items = self.receipt.items.all()
        self.assertEqual(str(items[0]), f"{self.receipt.number} - {items[0].product.name}")
        self.assertEqual(str(items[1]), f"{self.receipt.number} - {items[1].product.name}")
        self.assertEqual(str(items[2]), f"{self.receipt.number} - {items[2].product.name}")
