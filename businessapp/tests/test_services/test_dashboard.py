from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from ...models import (
    Category, Customer, Delivery, DeliveryItem, Product, ProductUnit, PurchaseOrder,
    PurchaseOrderItem, SalesOrder, SalesOrderItem, Supplier, Unit,
)
from ...services.dashboard import (
    TOP_WIDGET_LIMIT,
    active_purchase_orders_count,
    active_sales_orders_count,
    gross_margin_last_30_days,
    top_customers_by_recognized_revenue,
    top_data_payload,
    top_selling_products,
    slow_moving_products,
    total_revenue_last_30_days,
)


class DashboardMetricsServiceTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="dash", password="x")
        self.cat = Category.objects.create(name="C")
        self.unit = Unit.objects.create(name="u")
        self.product = Product.objects.create(
            name="P", category=self.cat, quantity=100, base_price=50
        )
        ProductUnit.objects.create(product=self.product, unit=self.unit, is_base_unit=True)
        self.customer = Customer.objects.create(name="Cust")
        self.supplier = Supplier.objects.create(name="Sup")

    def _confirm_so_with_delivery(self, total_days_offset=0):
        so = SalesOrder.objects.create(customer=self.customer)
        SalesOrderItem.objects.create(
            sales=so, product=self.product, unit=self.unit, quantity=2, price=Decimal("80")
        )
        so.delivery_date = timezone.now().date() + timedelta(days=1)
        so.save()
        so.confirm()
        d = so.deliveries.first()
        for item in d.items.all():
            item.quantity_delivered = item.quantity
            item.save()
        d.done(self.user)
        if total_days_offset:
            SalesOrder.objects.filter(pk=so.pk).update(
                created_at=timezone.now() - timedelta(days=total_days_offset)
            )
            Delivery.objects.filter(pk=d.pk).update(
                checked_at=timezone.now() - timedelta(days=total_days_offset)
            )
        return so, d

    def test_total_revenue_sums_confirmed_so_only_in_window(self):
        self._confirm_so_with_delivery(0)
        so2 = SalesOrder.objects.create(customer=self.customer)
        SalesOrderItem.objects.create(
            sales=so2, product=self.product, unit=self.unit, quantity=1, price=Decimal("20")
        )

        # Draft SO totals are excluded; only confirmed order (2 * 80 = 160)
        self.assertEqual(total_revenue_last_30_days(), Decimal("160"))

    def test_total_revenue_excludes_old_so(self):
        self._confirm_so_with_delivery(31)
        self.assertEqual(total_revenue_last_30_days(), Decimal("0"))

    def test_total_revenue_excludes_cancelled_so(self):
        self._confirm_so_with_delivery(0)
        so_cancelled = SalesOrder.objects.create(customer=self.customer)
        SalesOrderItem.objects.create(
            sales=so_cancelled,
            product=self.product,
            unit=self.unit,
            quantity=1,
            price=Decimal("999"),
        )
        so_cancelled.delivery_date = timezone.now().date() + timedelta(days=1)
        so_cancelled.save()
        so_cancelled.confirm()
        so_cancelled.cancel()

        self.assertEqual(total_revenue_last_30_days(), Decimal("160"))

    def test_gross_margin_uses_snapshot_cogs(self):
        self._confirm_so_with_delivery(0)

        # revenue 2*80=160, cogs 2*1*50=100
        self.assertEqual(gross_margin_last_30_days(), Decimal("60"))

    def test_gross_margin_zero_cogs_when_cost_snapshot_cleared(self):
        self._confirm_so_with_delivery(0)
        DeliveryItem.objects.update(base_unit_cost_snapshot=None)
        self.assertEqual(gross_margin_last_30_days(), Decimal("160"))

    def test_active_so_counts_confirmed_with_draft_delivery(self):
        so = SalesOrder.objects.create(customer=self.customer)
        SalesOrderItem.objects.create(
            sales=so, product=self.product, unit=self.unit, quantity=1, price=Decimal("10")
        )
        so.delivery_date = timezone.now().date() + timedelta(days=1)
        so.save()
        so.confirm()
        self.assertEqual(active_sales_orders_count(), 1)
        d = so.deliveries.first()
        d.done(self.user)
        self.assertEqual(active_sales_orders_count(), 0)

    def test_active_po_counts_confirmed_with_draft_receipt(self):
        po = PurchaseOrder.objects.create(supplier=self.supplier)
        PurchaseOrderItem.objects.create(
            purchase=po, product=self.product, unit=self.unit, quantity=1, price=Decimal("10")
        )
        po.arrival_date = timezone.now().date() + timedelta(days=1)
        po.save()
        po.confirm()
        self.assertEqual(active_purchase_orders_count(), 1)

    def test_active_so_excludes_draft_order(self):
        so = SalesOrder.objects.create(customer=self.customer)
        SalesOrderItem.objects.create(
            sales=so, product=self.product, unit=self.unit, quantity=1, price=Decimal("10")
        )
        self.assertEqual(active_sales_orders_count(), 0)


class DashboardEmptyServiceTest(TestCase):
    def test_metrics_and_top_lists_zero_or_empty_without_rows(self):
        self.assertEqual(total_revenue_last_30_days(), 0)
        self.assertEqual(gross_margin_last_30_days(), 0)
        self.assertEqual(active_sales_orders_count(), 0)
        self.assertEqual(active_purchase_orders_count(), 0)
        self.assertEqual(top_selling_products(), [])
        self.assertEqual(slow_moving_products(), [])
        self.assertEqual(top_customers_by_recognized_revenue(), [])


class DashboardTopDataServiceTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="topdata", password="x")
        self.cat = Category.objects.create(name="TopCat")
        self.unit = Unit.objects.create(name="pcs")
        self.product_hi = Product.objects.create(
            name="HighSeller", category=self.cat, quantity=100, base_price=10
        )
        self.product_lo = Product.objects.create(
            name="LowSeller", category=self.cat, quantity=100, base_price=20
        )
        for p in (self.product_hi, self.product_lo):
            ProductUnit.objects.create(product=p, unit=self.unit, is_base_unit=True)
        self.cust_a = Customer.objects.create(name="BuyerA")
        self.cust_b = Customer.objects.create(name="BuyerB")
        self.unit_box = Unit.objects.create(name="box")
        ProductUnit.objects.create(
            product=self.product_hi, unit=self.unit_box, multiplier=3
        )

    def _confirm_and_deliver(self, customer, product, quantity, price):
        so = SalesOrder.objects.create(customer=customer)
        SalesOrderItem.objects.create(
            sales=so, product=product, unit=self.unit, quantity=quantity, price=price
        )
        so.delivery_date = timezone.now().date() + timedelta(days=1)
        so.save()
        so.confirm()
        d = so.deliveries.first()
        for item in d.items.all():
            item.quantity_delivered = item.quantity
            item.save()
        d.done(self.user)
        return so, d

    def _confirm_and_deliver_with_unit(self, customer, product, unit, quantity, price):
        so = SalesOrder.objects.create(customer=customer)
        SalesOrderItem.objects.create(
            sales=so, product=product, unit=unit, quantity=quantity, price=price
        )
        so.delivery_date = timezone.now().date() + timedelta(days=1)
        so.save()
        so.confirm()
        d = so.deliveries.first()
        for item in d.items.all():
            item.quantity_delivered = item.quantity
            item.save()
        d.done(self.user)
        return so, d

    def test_top_selling_orders_by_base_qty_desc(self):
        self._confirm_and_deliver(self.cust_a, self.product_lo, 5, Decimal("30"))
        self._confirm_and_deliver(self.cust_a, self.product_hi, 2, Decimal("80"))
        rows = top_selling_products(limit=5)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], self.product_lo.id)
        self.assertEqual(rows[0]["sold_qty"], 5)
        self.assertEqual(rows[1]["id"], self.product_hi.id)
        self.assertEqual(rows[1]["sold_qty"], 2)

    def test_slow_moving_orders_by_base_qty_asc(self):
        self._confirm_and_deliver(self.cust_a, self.product_lo, 5, Decimal("30"))
        self._confirm_and_deliver(self.cust_a, self.product_hi, 2, Decimal("80"))
        rows = slow_moving_products(limit=5)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], self.product_hi.id)
        self.assertEqual(rows[0]["sold_qty"], 2)
        self.assertEqual(rows[1]["id"], self.product_lo.id)
        self.assertEqual(rows[1]["sold_qty"], 5)

    def test_top_customers_by_recognized_revenue_desc(self):
        # A: 2 * 80 = 160; B: 1 * 50 = 50
        self._confirm_and_deliver(self.cust_a, self.product_hi, 2, Decimal("80"))
        self._confirm_and_deliver(self.cust_b, self.product_lo, 1, Decimal("50"))
        rows = top_customers_by_recognized_revenue(limit=5)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], self.cust_a.id)
        self.assertEqual(rows[0]["total_purchased"], Decimal("160"))
        self.assertEqual(rows[1]["id"], self.cust_b.id)
        self.assertEqual(rows[1]["total_purchased"], Decimal("50"))

    def test_top_selling_converts_to_base_units_via_multiplier(self):
        # 1 box × mult 3 = 3 base units for product_hi
        self._confirm_and_deliver_with_unit(
            self.cust_a, self.product_hi, self.unit_box, 1, Decimal("99")
        )
        rows = top_selling_products(limit=5)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sold_qty"], 3)

    def test_top_selling_respects_limit(self):
        for i in range(TOP_WIDGET_LIMIT + 1):
            p = Product.objects.create(
                name=f"LimitP{i}", category=self.cat, quantity=100, base_price=1
            )
            ProductUnit.objects.create(product=p, unit=self.unit, is_base_unit=True)
            self._confirm_and_deliver(self.cust_a, p, 1, Decimal("1"))
        self.assertEqual(len(top_selling_products()), TOP_WIDGET_LIMIT)

    def test_top_widgets_exclude_fulfillments_outside_period(self):
        so, d = self._confirm_and_deliver(self.cust_a, self.product_hi, 1, Decimal("100"))
        Delivery.objects.filter(pk=d.pk).update(
            checked_at=timezone.now() - timedelta(days=31)
        )
        self.assertEqual(top_selling_products(), [])
        self.assertEqual(slow_moving_products(), [])
        self.assertEqual(top_customers_by_recognized_revenue(), [])

    def test_top_data_payload_has_expected_keys_and_types(self):
        self._confirm_and_deliver(self.cust_a, self.product_hi, 1, Decimal("10"))
        payload = top_data_payload()
        self.assertEqual(
            set(payload.keys()),
            {"top_selling_products", "slow_moving_products", "top_customers"},
        )
        self.assertIsInstance(payload["top_selling_products"], list)
        self.assertIsInstance(payload["slow_moving_products"], list)
        self.assertIsInstance(payload["top_customers"], list)
        self.assertEqual(len(payload["top_selling_products"]), 1)
        self.assertEqual(payload["top_selling_products"][0]["sold_qty"], 1)
