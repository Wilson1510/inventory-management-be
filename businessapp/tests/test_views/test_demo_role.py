from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ...models import (
    Category, Unit, Product, Customer, Supplier, SalesOrder, PurchaseOrder,
    Delivery, Receipt, User
)

class DemoRolePermissionsTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='admin', password='password123')
        self.demo_user = User.objects.create_user(
            username='demo_user', password='password123', role=User.Role.DEMO
        )
        
        # Create dummy data for detail views
        self.category = Category.objects.create(name='Test Category')
        self.unit = Unit.objects.create(name='Test Unit')
        self.product = Product.objects.create(name='Test Product', category=self.category)
        self.customer = Customer.objects.create(name='Test Customer')
        self.supplier = Supplier.objects.create(name='Test Supplier')
        self.sales_order = SalesOrder.objects.create(customer=self.customer)
        self.purchase_order = PurchaseOrder.objects.create(supplier=self.supplier)
        
        # Create Delivery and Receipt directly for testing endpoints
        self.delivery = Delivery.objects.create(
            sales_order=self.sales_order, delivery_date=timezone.now().date()
        )
        self.receipt = Receipt.objects.create(
            purchase_order=self.purchase_order, arrival_date=timezone.now().date()
        )

    def assert_read_only_access(self, list_url, detail_url=None, post_url=None):
        self.client.force_authenticate(user=self.demo_user)
        
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.post(list_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        if detail_url:
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            response = self.client.patch(detail_url, {})
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            
            response = self.client.delete(detail_url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            
        if post_url:
            response = self.client.post(post_url, {})
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_category_permissions(self):
        self.assert_read_only_access(
            reverse('category-list'),
            reverse('category-detail', args=[self.category.pk])
        )

    def test_unit_permissions(self):
        self.assert_read_only_access(
            reverse('unit-list'),
            reverse('unit-detail', args=[self.unit.pk])
        )

    def test_product_permissions(self):
        self.assert_read_only_access(
            reverse('product-list'),
            reverse('product-detail', args=[self.product.pk])
        )

    def test_customer_permissions(self):
        self.assert_read_only_access(
            reverse('customer-list'),
            reverse('customer-detail', args=[self.customer.pk])
        )

    def test_supplier_permissions(self):
        self.assert_read_only_access(
            reverse('supplier-list'),
            reverse('supplier-detail', args=[self.supplier.pk])
        )

    def test_sales_order_permissions(self):
        self.assert_read_only_access(
            reverse('salesorder-list'),
            reverse('salesorder-detail', args=[self.sales_order.pk]),
            post_url=reverse('salesorder-cancel', args=[self.sales_order.pk])
        )

    def test_purchase_order_permissions(self):
        self.assert_read_only_access(
            reverse('purchaseorder-list'),
            reverse('purchaseorder-detail', args=[self.purchase_order.pk]),
            post_url=reverse('purchaseorder-cancel', args=[self.purchase_order.pk])
        )

    def test_delivery_permissions(self):
        self.assert_read_only_access(
            reverse('delivery-list'),
            reverse('delivery-detail', args=[self.delivery.pk]),
            post_url=reverse('delivery-done', args=[self.delivery.pk])
        )

    def test_receipt_permissions(self):
        self.assert_read_only_access(
            reverse('receipt-list'),
            reverse('receipt-detail', args=[self.receipt.pk]),
            post_url=reverse('receipt-done', args=[self.receipt.pk])
        )

    def test_dashboard_permissions(self):
        self.client.force_authenticate(user=self.demo_user)
        # Dashboard only has GET endpoints
        response = self.client.get(reverse('dashboard-metrics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get(reverse('dashboard-top-data'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_permissions(self):
        self.client.force_authenticate(user=self.demo_user)
        
        # User list
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User POST
        response = self.client.post(reverse('user-list'), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # User me GET
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User me PATCH
        response = self.client.patch(reverse('user-me'), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # User change-password PATCH
        response = self.client.patch(reverse('user-change-password'), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
