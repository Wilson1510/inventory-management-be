from django.test import TestCase
from invensys.models import (
    SalesOrder, SalesOrderItem, Product, Customer, Category, Unit, ProductUnit, Delivery
)
from django.utils import timezone
from datetime import timedelta


class BaseSaleOrderTest(TestCase):
    def setUp(self):
        self.units = Unit.objects.bulk_create([
            Unit(name='Test Unit 1'),
            Unit(name='Test Unit 2'),
            Unit(name='Test Unit 3'),
        ])
        self.categories = Category.objects.create(name='Test Category')
        self.products = [
            Product.objects.create(
                name='Test Product 1', category=self.categories, quantity=10, base_price=100
            ),
            Product.objects.create(
                name='Test Product 2', category=self.categories, quantity=20, base_price=200
            ),
            Product.objects.create(
                name='Test Product 3', category=self.categories, quantity=30, base_price=300
            ),
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
        self.customer = Customer.objects.create(name='Test Customer')
        self.sales_order = SalesOrder.objects.create(customer=self.customer)
        self.sales_order_items = [
            SalesOrderItem.objects.create(
                sales=self.sales_order,
                product=self.products[0],
                price=100,
            ),
            SalesOrderItem.objects.create(
                sales=self.sales_order,
                product=self.products[1],
                quantity=20,
                price=200,
            ),
            SalesOrderItem.objects.create(
                sales=self.sales_order,
                product=self.products[2],
                quantity=3,
                price=300,
                unit=self.units[0],
            ),
        ]

    def fill_delivery_date(self):
        delivery_date = timezone.now().date() + timedelta(days=1)
        self.sales_order.delivery_date = delivery_date
        self.sales_order.save()


class SalesOrderModelTest(BaseSaleOrderTest):
    def test_number_is_generated_when_order_is_created(self):
        self.assertEqual(self.sales_order.number, f"SO{self.sales_order.pk:05d}")

    def test_status_is_set_to_draft_by_default(self):
        self.assertEqual(self.sales_order.status, SalesOrder.Status.DRAFT)

    def test_total_is_0_by_default(self):
        so = SalesOrder.objects.create(customer=self.customer)
        self.assertEqual(so.total, 0)

    def test_total_is_calculated_when_order_item_is_saved(self):
        self.assertEqual(self.sales_order.total, 5000)
        self.sales_order_items[0].quantity += 1
        self.sales_order_items[0].save()
        self.assertEqual(self.sales_order.total, 5100)

    def test_total_is_calculated_when_order_item_is_deleted(self):
        self.assertEqual(self.sales_order.total, 5000)
        self.sales_order_items[0].delete()
        self.assertEqual(self.sales_order.total, 4900)

    def test_order_item_unit_is_set_to_base_unit_if_not_set(self):
        self.assertEqual(self.sales_order_items[0].unit, self.units[0])
        self.assertEqual(self.sales_order_items[1].unit, self.units[1])

    def test_order_item_unit_is_set_to_other_unit_if_set(self):
        self.assertEqual(self.sales_order_items[2].unit, self.units[0])

    def test_cannot_confirm_order_with_no_items(self):
        so = SalesOrder.objects.create(customer=self.customer)
        with self.assertRaises(ValueError):
            so.confirm()

    def test_cannot_confirm_order_with_zero_quantity(self):
        so = SalesOrder.objects.create(customer=self.customer)
        SalesOrderItem.objects.create(sales=so, product=self.products[0], quantity=0, price=100)
        with self.assertRaises(ValueError):
            so.confirm()

    def test_cannot_confirm_order_with_negative_quantity(self):
        so = SalesOrder.objects.create(customer=self.customer)
        SalesOrderItem.objects.create(sales=so, product=self.products[0], quantity=-1, price=100)
        with self.assertRaises(ValueError):
            so.confirm()

    def test_cannot_confirm_order_with_delivery_date_in_the_past(self):
        delivery_date = timezone.now().date() - timedelta(days=1)
        self.sales_order.delivery_date = delivery_date
        self.sales_order.save()
        with self.assertRaises(ValueError):
            self.sales_order.confirm()

    def test_cannot_confirm_order_with_delivery_date_not_set(self):
        with self.assertRaises(ValueError):
            self.sales_order.confirm()

    def test_rollback_status_when_confirming_order_fails(self):
        self.fill_delivery_date()

        def error_method():
            raise ValueError("Test error")

        self.sales_order._create_delivery_order_and_items = error_method
        with self.assertRaises(ValueError):
            self.sales_order.confirm()
        self.sales_order.refresh_from_db()

        self.assertEqual(self.sales_order.status, SalesOrder.Status.DRAFT)
        self.assertEqual(self.sales_order.deliveries.count(), 0)

    def test_status_is_confirmed_when_order_is_confirmed(self):
        self.fill_delivery_date()
        self.sales_order.confirm()
        self.assertEqual(self.sales_order.status, SalesOrder.Status.CONFIRMED)

    def test_delivery_order_is_created_when_order_is_confirmed(self):
        self.fill_delivery_date()
        self.sales_order.confirm()

        delivery_created = self.sales_order.deliveries
        self.assertEqual(delivery_created.count(), 1)
        self.assertEqual(delivery_created.first().delivery_date, self.sales_order.delivery_date)
        self.assertEqual(delivery_created.first().status, Delivery.Status.DRAFT)
        self.assertEqual(delivery_created.first().sales_order, self.sales_order)

    def test_delivery_items_are_created_and_same_as_order_items_when_order_is_confirmed(self):
        self.fill_delivery_date()
        self.sales_order.confirm()

        delivery_created = self.sales_order.deliveries
        self.assertEqual(delivery_created.first().items.count(), 3)
        self.assertEqual(delivery_created.first().items.first().product, self.products[0])
        self.assertEqual(delivery_created.first().items.first().quantity, 1)
        self.assertEqual(delivery_created.first().items.first().price, 100)
        self.assertEqual(delivery_created.first().items.first().unit, self.units[0])

    def test_status_is_cancelled_when_order_is_cancelled(self):
        self.sales_order.cancel()
        self.assertEqual(self.sales_order.status, SalesOrder.Status.CANCELLED)

    def test_deliveries_are_cancelled_when_order_is_cancelled(self):
        self.fill_delivery_date()
        self.sales_order.confirm()
        self.sales_order.cancel()
        deliveries = self.sales_order.deliveries
        for delivery in deliveries.all():
            self.assertEqual(delivery.status, Delivery.Status.CANCELLED)

    def test_cannot_cancel_order_with_done_deliveries(self):
        self.fill_delivery_date()
        self.sales_order.confirm()
        deliveries = self.sales_order.deliveries

        for item in deliveries.first().items.all():
            item.quantity_delivered = item.quantity
            item.save()

        self.sales_order.deliveries.first().done()
        with self.assertRaises(ValueError):
            self.sales_order.cancel()

    def test_so_str_returns_number(self):
        self.assertEqual(str(self.sales_order), self.sales_order.number)

    def test_so_item_str_returns_sales_order_number_and_product_name(self):
        self.assertEqual(
            str(self.sales_order_items[0]), f"{self.sales_order.number} - {self.products[0].name}"
        )
        self.assertEqual(
            str(self.sales_order_items[1]), f"{self.sales_order.number} - {self.products[1].name}"
        )
        self.assertEqual(
            str(self.sales_order_items[2]), f"{self.sales_order.number} - {self.products[2].name}"
        )
