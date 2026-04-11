from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ...models import Customer, Supplier, SalesOrder, PurchaseOrder


class CustomerViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='user', password='password123')
        self.customer = Customer.objects.create(name='Test Customer')
        self.list_url = reverse('customer-list')
        self.detail_url = reverse('customer-detail', kwargs={'pk': self.customer.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_customers_list(self):
        SalesOrder.objects.create(
            customer=self.customer, total=1000000, status=SalesOrder.Status.CONFIRMED
        )
        last_confirmed_sale_order = SalesOrder.objects.create(
            customer=self.customer, total=2000000, status=SalesOrder.Status.CONFIRMED
        )
        SalesOrder.objects.create(
            customer=self.customer, total=3000000, status=SalesOrder.Status.DRAFT
        )
        SalesOrder.objects.create(
            customer=self.customer, total=4000000, status=SalesOrder.Status.CANCELLED
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['count_sale_orders'], 2)
        self.assertEqual(response.data[0]['total_sale_amount'], '3000000.00')
        self.assertEqual(
            response.data[0]['last_sale_order_date'],
            last_confirmed_sale_order.created_at.isoformat().replace("+00:00", "Z")
        )

    def test_get_customer_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.customer.name)

    def test_create_customer(self):
        self.client.force_authenticate(user=self.user)
        data = {'name': 'Test Customer 2'}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_customer = Customer.objects.get(name='Test Customer 2')
        self.assertEqual(new_customer.name, 'Test Customer 2')

    def test_update_customer(self):
        self.client.force_authenticate(user=self.user)
        data = {'name': 'Test Customer Updated'}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_customer = Customer.objects.get(name='Test Customer Updated')
        self.assertEqual(new_customer.name, 'Test Customer Updated')

    def test_delete_customer(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())


class SupplierViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='user', password='password123')
        self.supplier = Supplier.objects.create(name='Test Supplier')
        self.list_url = reverse('supplier-list')
        self.detail_url = reverse('supplier-detail', kwargs={'pk': self.supplier.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_suppliers_list(self):
        PurchaseOrder.objects.create(
            supplier=self.supplier, total=1000000, status=PurchaseOrder.Status.CONFIRMED
        )
        last_confirmed_purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier, total=2000000, status=PurchaseOrder.Status.CONFIRMED
        )
        PurchaseOrder.objects.create(
            supplier=self.supplier, total=3000000, status=PurchaseOrder.Status.DRAFT
        )
        PurchaseOrder.objects.create(
            supplier=self.supplier, total=4000000, status=PurchaseOrder.Status.CANCELLED
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['count_purchase_orders'], 2)
        self.assertEqual(response.data[0]['total_purchase_amount'], '3000000.00')
        self.assertEqual(
            response.data[0]['last_purchase_order_date'],
            last_confirmed_purchase_order.created_at.isoformat().replace("+00:00", "Z")
        )

    def test_get_supplier_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.supplier.name)

    def test_create_supplier(self):
        self.client.force_authenticate(user=self.user)
        data = {'name': 'Test Supplier 2'}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_supplier = Supplier.objects.get(name='Test Supplier 2')
        self.assertEqual(new_supplier.name, 'Test Supplier 2')

    def test_update_supplier(self):
        self.client.force_authenticate(user=self.user)
        data = {'name': 'Test Supplier Updated'}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_supplier = Supplier.objects.get(name='Test Supplier Updated')
        self.assertEqual(new_supplier.name, 'Test Supplier Updated')

    def test_delete_supplier(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Supplier.objects.filter(pk=self.supplier.pk).exists())
