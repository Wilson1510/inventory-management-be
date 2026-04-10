from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ...models import Category, Customer, Product, ProductUnit, SalesOrder, SalesOrderItem, Unit


class DashboardAPITest(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(username="api_dash", password="x")
        self.client.force_authenticate(user=self.user)
        self.metrics_url = reverse("dashboard-metrics")
        self.top_url = reverse("dashboard-top-data")

    def test_metrics_requires_auth(self):
        self.client.force_authenticate(user=None)
        r = self.client.get(self.metrics_url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_top_data_requires_auth(self):
        self.client.force_authenticate(user=None)
        r = self.client.get(self.top_url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_metrics_empty_returns_zero_values(self):
        r = self.client.get(self.metrics_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["total_revenue"], "0.00")
        self.assertEqual(r.data["gross_margin"], "0.00")
        self.assertEqual(r.data["active_sales_orders"], 0)
        self.assertEqual(r.data["active_purchase_orders"], 0)

    def test_top_data_empty_returns_empty_lists(self):
        r = self.client.get(self.top_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["top_selling_products"], [])
        self.assertEqual(r.data["slow_moving_products"], [])
        self.assertEqual(r.data["top_customers"], [])

    def _seed_one_confirmed_fulfilled_sale(self):
        cat = Category.objects.create(name="ApiCat")
        unit = Unit.objects.create(name="api-u")
        product = Product.objects.create(
            name="ApiProd", category=cat, quantity=50, base_price=Decimal("10")
        )
        ProductUnit.objects.create(product=product, unit=unit, is_base_unit=True)
        customer = Customer.objects.create(name="ApiBuyer")
        so = SalesOrder.objects.create(customer=customer)
        SalesOrderItem.objects.create(
            sales=so, product=product, unit=unit, quantity=2, price=Decimal("25")
        )
        so.delivery_date = timezone.now().date() + timedelta(days=1)
        so.save()
        so.confirm()
        delivery = so.deliveries.first()
        for item in delivery.items.all():
            item.quantity_delivered = item.quantity
            item.save()
        delivery.done(self.user)
        product.refresh_from_db()
        return product, customer

    def test_metrics_data_exists_returns_expected_values(self):
        self._seed_one_confirmed_fulfilled_sale()
        r = self.client.get(self.metrics_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Confirmed SO total 2 * 25; margin = recognized revenue 50 - COGS 2 * 10
        self.assertEqual(r.data["total_revenue"], "50.00")
        self.assertEqual(r.data["gross_margin"], "30.00")
        self.assertEqual(r.data["active_sales_orders"], 0)
        self.assertEqual(r.data["active_purchase_orders"], 0)

    def test_top_data_data_exists_returns_expected_values(self):
        product, customer = self._seed_one_confirmed_fulfilled_sale()
        r = self.client.get(self.top_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        row = {
            "id": product.id,
            "sku_number": product.sku_number,
            "name": "ApiProd",
            "sold_qty": 2,
        }
        self.assertEqual(r.data["top_selling_products"], [row])
        self.assertEqual(r.data["slow_moving_products"], [row])
        self.assertEqual(
            r.data["top_customers"],
            [
                {
                    "id": customer.id,
                    "name": "ApiBuyer",
                    "total_purchased": "50.00",
                }
            ],
        )
