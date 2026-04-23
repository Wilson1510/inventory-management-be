from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from ...models import (
    Category,
    Customer,
    Product,
    ProductUnit,
    PurchaseOrder,
    PurchaseOrderItem,
    SalesOrder,
    SalesOrderItem,
    Supplier,
    Unit,
)


class SalesOrderViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_a = User.objects.create_superuser(username='admin_a', password='password123')
        self.admin_b = User.objects.create_superuser(username='admin_b', password='password123')
        self.category = Category.objects.create(name='Cat', created_by=self.admin_a)
        self.unit = Unit.objects.create(name='pcs')
        self.unit2 = Unit.objects.create(name='box')
        self.product = Product.objects.create(
            name='Item A',
            category=self.category,
            created_by=self.admin_a,
            updated_by=self.admin_a,
        )
        self.product2 = Product.objects.create(
            name='Item B',
            category=self.category,
            created_by=self.admin_a,
            updated_by=self.admin_a,
        )
        ProductUnit.objects.create(
            product=self.product,
            unit=self.unit,
            multiplier=1,
            is_base_unit=True,
        )
        ProductUnit.objects.create(
            product=self.product2,
            unit=self.unit2,
            multiplier=1,
            is_base_unit=True,
        )

        self.customer = Customer.objects.create(name='Buyer', created_by=self.admin_a)
        self.sales_order = SalesOrder.objects.create(
            customer=self.customer,
            created_by=self.admin_a,
            updated_by=self.admin_a,
        )
        self.so_item = SalesOrderItem.objects.create(
            sales=self.sales_order,
            product=self.product,
            unit=self.unit,
            quantity=2,
            price=Decimal('15.00'),
        )
        self.so_item2 = SalesOrderItem.objects.create(
            sales=self.sales_order,
            product=self.product2,
            unit=self.unit2,
            quantity=3,
            price=Decimal('10.00'),
        )

        self.list_url = reverse('salesorder-list')
        self.detail_url = reverse('salesorder-detail', kwargs={'pk': self.sales_order.pk})
        self.confirm_url = reverse('salesorder-confirm', kwargs={'pk': self.sales_order.pk})
        self.cancel_url = reverse('salesorder-cancel', kwargs={'pk': self.sales_order.pk})

    def _future_date_str(self):
        return str(timezone.now().date() + timedelta(days=7))

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_access_denied(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='password123')
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_sales_orders_list(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row['number'], self.sales_order.number)
        self.assertEqual(row['customer']['name'], 'Buyer')
        self.assertEqual(Decimal(str(row['total'])), Decimal('60.00'))

    def test_get_sales_order_detail(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], self.sales_order.number)
        self.assertEqual(response.data['customer']['name'], 'Buyer')
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 2)
        self.assertEqual(response.data['items'][0]['product']['name'], 'Item A')
        self.assertEqual(response.data['items'][0]['unit']['name'], 'pcs')

    def test_create_sales_order(self):
        self.client.force_authenticate(user=self.admin_a)
        payload = {
            'customer_id': self.customer.pk,
            'delivery_date': self._future_date_str(),
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 1,
                    'price': '99.00',
                    'unit_id': self.unit.pk,
                },
            ],
        }
        response = self.client.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = SalesOrder.objects.get(pk=response.data['id'])
        self.assertEqual(created.customer, self.customer)
        self.assertEqual(created.items.count(), 1)
        self.assertEqual(created.created_by, self.admin_a)

        item = created.items.first()
        self.assertEqual(item.created_by, self.admin_a)
        self.assertEqual(item.updated_by, self.admin_a)

    def test_update_sales_order(self):
        self.client.force_authenticate(user=self.admin_b)
        payload = {
            'customer_id': self.customer.pk,
            'delivery_date': self._future_date_str(),
            'items': [
                {
                    'id': self.so_item.pk,
                    'product_id': self.product2.pk,
                    'quantity': 3,
                    'price': '10.00',
                    'unit_id': self.unit2.pk,
                },
                {
                    'product_id': self.product.pk,
                    'quantity': 1,
                    'price': '5.00',
                    'unit_id': self.unit.pk,
                },
            ],
        }
        response = self.client.put(self.detail_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sales_order.refresh_from_db()
        self.assertEqual(self.sales_order.customer, self.customer)
        self.assertEqual(self.sales_order.items.count(), 2)
        
        existing_item = self.sales_order.items.get(pk=self.so_item.pk)
        self.assertEqual(existing_item.price, Decimal('10.00'))
        self.assertEqual(existing_item.updated_by, self.admin_b)
        
        new_item = self.sales_order.items.filter(quantity=1, price=Decimal('5.00')).first()
        self.assertIsNotNone(new_item)
        self.assertEqual(new_item.created_by, self.admin_b)
        self.assertEqual(new_item.updated_by, self.admin_b)
        
        self.assertFalse(self.sales_order.items.filter(pk=self.so_item2.pk).exists())

    def test_partial_update_sales_order(self):
        self.client.force_authenticate(user=self.admin_b)
        new_date = self._future_date_str()
        payload = {'delivery_date': new_date}
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sales_order.refresh_from_db()
        self.assertEqual(str(self.sales_order.delivery_date), new_date)
        self.assertEqual(self.sales_order.items.count(), 2)

    def test_delete_sales_order(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SalesOrder.objects.filter(pk=self.sales_order.pk).exists())

    def test_confirm_sales_order_success(self):
        self.sales_order.delivery_date = timezone.now().date() + timedelta(days=1)
        self.sales_order.save()
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.sales_order.refresh_from_db()
        self.assertEqual(self.sales_order.status, SalesOrder.Status.CONFIRMED)

    def test_confirm_sales_order_bad_request(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.sales_order.refresh_from_db()
        self.assertEqual(self.sales_order.status, SalesOrder.Status.DRAFT)

    def test_cancel_sales_order(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sales_order.refresh_from_db()
        self.assertEqual(self.sales_order.status, SalesOrder.Status.CANCELLED)

    def test_cancel_sales_order_bad_request(self):
        with patch('invensys.views.SalesOrder.cancel') as mock_cancel:
            mock_cancel.side_effect = ValueError("Test error")
            self.client.force_authenticate(user=self.admin_a)
            response = self.client.post(self.cancel_url)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('detail', response.data)
            self.sales_order.refresh_from_db()
            self.assertEqual(self.sales_order.status, SalesOrder.Status.DRAFT)

    def test_invalid_create_sales_order(self):
        self.client.force_authenticate(user=self.admin_a)
        payload = {
            'customer_id': 99999,
            'delivery_date': self._future_date_str(),
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 1,
                    'price': '1.00',
                    'unit_id': self.unit.pk,
                },
            ],
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer_id', response.data)


class PurchaseOrderViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_a = User.objects.create_superuser(username='admin_a', password='password123')
        self.admin_b = User.objects.create_superuser(username='admin_b', password='password123')

        self.category = Category.objects.create(name='Cat', created_by=self.admin_a)
        self.unit = Unit.objects.create(name='pcs')
        self.unit2 = Unit.objects.create(name='box')
        self.product = Product.objects.create(
            name='Item A',
            category=self.category,
            created_by=self.admin_a,
            updated_by=self.admin_a,
        )
        self.product2 = Product.objects.create(
            name='Item B',
            category=self.category,
            created_by=self.admin_a,
            updated_by=self.admin_a,
        )
        ProductUnit.objects.create(
            product=self.product,
            unit=self.unit,
            multiplier=1,
            is_base_unit=True,
        )
        ProductUnit.objects.create(
            product=self.product2,
            unit=self.unit2,
            multiplier=1,
            is_base_unit=True,
        )

        self.supplier = Supplier.objects.create(name='Vendor', created_by=self.admin_a)
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            created_by=self.admin_a,
            updated_by=self.admin_a,
        )
        self.po_item = PurchaseOrderItem.objects.create(
            purchase=self.purchase_order,
            product=self.product,
            unit=self.unit,
            quantity=2,
            price=Decimal('15.00'),
        )
        self.po_item2 = PurchaseOrderItem.objects.create(
            purchase=self.purchase_order,
            product=self.product2,
            unit=self.unit2,
            quantity=3,
            price=Decimal('10.00'),
        )

        self.list_url = reverse('purchaseorder-list')
        self.detail_url = reverse('purchaseorder-detail', kwargs={'pk': self.purchase_order.pk})
        self.confirm_url = reverse('purchaseorder-confirm', kwargs={'pk': self.purchase_order.pk})
        self.cancel_url = reverse('purchaseorder-cancel', kwargs={'pk': self.purchase_order.pk})

    def _future_date_str(self):
        return str(timezone.now().date() + timedelta(days=7))

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_access_denied(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='password123')
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_purchase_orders_list(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row['number'], self.purchase_order.number)
        self.assertEqual(row['supplier']['name'], 'Vendor')
        self.assertEqual(Decimal(str(row['total'])), Decimal('60.00'))

    def test_get_purchase_order_detail(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], self.purchase_order.number)
        self.assertEqual(response.data['supplier']['name'], 'Vendor')
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 2)
        self.assertEqual(response.data['items'][0]['product']['name'], 'Item A')

    def test_create_purchase_order(self):
        self.client.force_authenticate(user=self.admin_a)
        payload = {
            'supplier_id': self.supplier.pk,
            'arrival_date': self._future_date_str(),
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 1,
                    'price': '99.00',
                    'unit_id': self.unit.pk,
                },
            ],
        }
        response = self.client.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = PurchaseOrder.objects.get(pk=response.data['id'])
        self.assertEqual(created.supplier, self.supplier)
        self.assertEqual(created.items.count(), 1)
        self.assertEqual(created.created_by, self.admin_a)

        item = created.items.first()
        self.assertEqual(item.created_by, self.admin_a)
        self.assertEqual(item.updated_by, self.admin_a)

    def test_update_purchase_order(self):
        self.client.force_authenticate(user=self.admin_b)
        payload = {
            'supplier_id': self.supplier.pk,
            'arrival_date': self._future_date_str(),
            'items': [
                {
                    'id': self.po_item.pk,
                    'product_id': self.product2.pk,
                    'quantity': 3,
                    'price': '10.00',
                    'unit_id': self.unit2.pk,
                },
                {
                    'product_id': self.product.pk,
                    'quantity': 1,
                    'price': '5.00',
                    'unit_id': self.unit.pk,
                },
            ],
        }
        response = self.client.put(self.detail_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.purchase_order.refresh_from_db()
        self.assertEqual(self.purchase_order.items.count(), 2)
        
        existing_item = self.purchase_order.items.get(pk=self.po_item.pk)
        self.assertEqual(existing_item.price, Decimal('10.00'))
        self.assertEqual(existing_item.updated_by, self.admin_b)
        
        new_item = self.purchase_order.items.filter(quantity=1, price=Decimal('5.00')).first()
        self.assertIsNotNone(new_item)
        self.assertEqual(new_item.created_by, self.admin_b)
        self.assertEqual(new_item.updated_by, self.admin_b)

        self.assertFalse(self.purchase_order.items.filter(pk=self.po_item2.pk).exists())

    def test_partial_update_purchase_order(self):
        self.client.force_authenticate(user=self.admin_b)
        new_date = self._future_date_str()
        payload = {'arrival_date': new_date}
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.purchase_order.refresh_from_db()
        self.assertEqual(str(self.purchase_order.arrival_date), new_date)
        self.assertEqual(self.purchase_order.items.count(), 2)

    def test_delete_purchase_order(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PurchaseOrder.objects.filter(pk=self.purchase_order.pk).exists())

    def test_confirm_purchase_order_success(self):
        self.purchase_order.arrival_date = timezone.now().date() + timedelta(days=1)
        self.purchase_order.save()
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.purchase_order.refresh_from_db()
        self.assertEqual(self.purchase_order.status, PurchaseOrder.Status.CONFIRMED)

    def test_confirm_purchase_order_bad_request(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.purchase_order.refresh_from_db()
        self.assertEqual(self.purchase_order.status, PurchaseOrder.Status.DRAFT)

    def test_cancel_purchase_order(self):
        self.client.force_authenticate(user=self.admin_a)
        response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.purchase_order.refresh_from_db()
        self.assertEqual(self.purchase_order.status, PurchaseOrder.Status.CANCELLED)

    def test_cancel_purchase_order_bad_request(self):
        with patch('invensys.views.PurchaseOrder.cancel') as mock_cancel:
            mock_cancel.side_effect = ValueError("Test error")
            self.client.force_authenticate(user=self.admin_a)
            response = self.client.post(self.cancel_url)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('detail', response.data)
            self.purchase_order.refresh_from_db()
            self.assertEqual(self.purchase_order.status, PurchaseOrder.Status.DRAFT)

    def test_invalid_create_purchase_order(self):
        self.client.force_authenticate(user=self.admin_a)
        payload = {
            'supplier_id': 99999,
            'arrival_date': self._future_date_str(),
            'items': [
                {
                    'product_id': self.product.pk,
                    'quantity': 1,
                    'price': '1.00',
                    'unit_id': self.unit.pk,
                },
            ],
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('supplier_id', response.data)
