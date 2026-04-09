from django.contrib.auth import get_user_model

from .test_sale_order import BaseSaleOrderTest
from invensys.models import Delivery


class DeliveryModelTest(BaseSaleOrderTest):
    def setUp(self):
        super().setUp()
        self.check_user = get_user_model().objects.create_user(
            username='delivery_checker', password='x'
        )
        self.fill_delivery_date()
        self.sales_order.confirm()
        self.delivery = self.sales_order.deliveries.first()

    def fill_quantity_delivered(self):
        for item in self.delivery.items.all():
            item.quantity_delivered = item.quantity
            item.save()

    def test_number_is_generated_when_delivery_is_created(self):
        self.assertEqual(self.delivery.number, f"DO{self.delivery.pk:05d}")

    def test_status_is_set_to_draft_by_default(self):
        self.assertEqual(self.delivery.status, Delivery.Status.DRAFT)

    def test_checked_at_and_checked_by_are_null_by_default(self):
        self.assertIsNone(self.delivery.checked_at)
        self.assertIsNone(self.delivery.checked_by)

    def test_status_is_set_to_done_when_delivery_is_done(self):
        self.delivery.done(self.check_user)
        self.assertEqual(self.delivery.status, Delivery.Status.DONE)

    def test_checked_at_and_checked_by_are_set_when_delivery_is_done(self):
        self.delivery.done(self.check_user)
        self.assertIsNotNone(self.delivery.checked_at)
        self.assertEqual(self.delivery.checked_by, self.check_user)

    def test_product_quantity_is_subtracted_when_delivery_is_done(self):
        self.fill_quantity_delivered()
        self.assertEqual(self.products[0].quantity, 10)
        self.delivery.done(self.check_user)
        self.products[0].refresh_from_db()
        self.assertEqual(self.products[0].quantity, 9)

    def test_product_base_price_is_zero_when_delivery_is_done_and_product_quantity_is_zero(self):
        self.fill_quantity_delivered()
        self.assertEqual(self.products[1].base_price, 200)
        self.delivery.done(self.check_user)
        self.products[1].refresh_from_db()
        self.assertEqual(self.products[1].base_price, 0)

    def test_product_base_price_is_not_adjusted_when_delivery_is_done_and_product_quantity_is_not_zero(self):  # noqa: E501
        self.assertEqual(self.products[0].base_price, 100)
        self.delivery.done(self.check_user)
        self.products[0].refresh_from_db()
        self.assertEqual(self.products[0].base_price, 100)

    def test_cannot_done_delivery_with_quantity_delivered_greater_than_quantity(self):
        for item in self.delivery.items.all():
            item.quantity_delivered = item.quantity + 1
            item.save()
        with self.assertRaises(ValueError):
            self.delivery.done(self.check_user)

    def test_cannot_done_delivery_with_stock_is_not_available(self):
        product = self.delivery.items.first().product
        product.quantity = 0
        product.save()
        product.refresh_from_db()

        self.fill_quantity_delivered()

        with self.assertRaises(ValueError):
            self.delivery.done(self.check_user)

    def test_done_requires_user(self):
        self.fill_quantity_delivered()
        with self.assertRaises(ValueError):
            self.delivery.done(None)

    def test_status_is_set_to_cancelled_when_delivery_is_cancelled(self):
        self.delivery.cancel()
        self.assertEqual(self.delivery.status, Delivery.Status.CANCELLED)

    def test_delivery_item_get_multiplier_returns_multiplier(self):
        items = self.delivery.items.all()
        self.assertEqual(items[0].get_multiplier(), 1)
        self.assertEqual(items[1].get_multiplier(), 1)
        self.assertEqual(items[2].get_multiplier(), 4)

    def test_str_returns_number(self):
        self.assertEqual(str(self.delivery), self.delivery.number)

    def test_delivery_item_str_returns_delivery_number_and_product_name(self):
        items = self.delivery.items.all()
        self.assertEqual(str(items[0]), f"{self.delivery.number} - {items[0].product.name}")
        self.assertEqual(str(items[1]), f"{self.delivery.number} - {items[1].product.name}")
        self.assertEqual(str(items[2]), f"{self.delivery.number} - {items[2].product.name}")
