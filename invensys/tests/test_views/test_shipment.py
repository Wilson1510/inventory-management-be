from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ...models import (
    Category,
    Customer,
    Delivery,
    Product,
    ProductUnit,
    PurchaseOrder,
    PurchaseOrderItem,
    Receipt,
    SalesOrder,
    SalesOrderItem,
    Supplier,
    Unit,
)


class DeliveryViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user_a = User.objects.create_user(username='usera_dlv', password='password123')

        self.category = Category.objects.create(name='Cat', created_by=self.user_a)
        self.unit = Unit.objects.create(name='pcs')
        self.unit2 = Unit.objects.create(name='box')
        self.product = Product.objects.create(
            name='Item A',
            category=self.category,
            quantity=100,
            created_by=self.user_a,
            updated_by=self.user_a,
        )
        self.product2 = Product.objects.create(
            name='Item B',
            category=self.category,
            quantity=100,
            created_by=self.user_a,
            updated_by=self.user_a,
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

        self.customer = Customer.objects.create(
            name='Buyer',
            address='99 Ship St',
            created_by=self.user_a,
        )
        self.sales_order = SalesOrder.objects.create(
            customer=self.customer,
            created_by=self.user_a,
            updated_by=self.user_a,
        )
        SalesOrderItem.objects.create(
            sales=self.sales_order,
            product=self.product,
            unit=self.unit,
            quantity=2,
            price=Decimal('15.00'),
        )
        SalesOrderItem.objects.create(
            sales=self.sales_order,
            product=self.product2,
            unit=self.unit2,
            quantity=3,
            price=Decimal('10.00'),
        )

        future = timezone.now().date() + timedelta(days=7)
        self.sales_order.delivery_date = future
        self.sales_order.save()
        self.sales_order.confirm()

        self.delivery = self.sales_order.deliveries.get()
        self.d_items = list(self.delivery.items.order_by('pk'))

        self.list_url = reverse('delivery-list')
        self.detail_url = reverse('delivery-detail', kwargs={'pk': self.delivery.pk})
        self.done_url = reverse('delivery-done', kwargs={'pk': self.delivery.pk})
        self.cancel_url = reverse('delivery-cancel', kwargs={'pk': self.delivery.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_not_allowed(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.list_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_deliveries_list(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row['number'], self.delivery.number)
        self.assertEqual(row['sales_order']['id'], self.sales_order.pk)
        self.assertEqual(row['sales_order']['number'], self.sales_order.number)

    def test_get_delivery_detail(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], self.delivery.number)
        self.assertEqual(response.data['destination'], '99 Ship St')
        self.assertEqual(len(response.data['items']), 2)

    def test_patch_delivery(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'notes': 'Fragile',
            'method': Delivery.ShipmentMethod.PICKUP,
            'items': [
                {
                    'id': self.d_items[0].pk,
                    'quantity_delivered': 2,
                    'notes': 'Full',
                },
                {
                    'id': self.d_items[1].pk,
                    'quantity_delivered': 1,
                    'notes': 'Partial',
                },
            ],
        }
        response = self.client.patch(self.detail_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.notes, 'Fragile')
        self.assertEqual(self.delivery.method, Delivery.ShipmentMethod.PICKUP)
        self.d_items[0].refresh_from_db()
        self.d_items[1].refresh_from_db()
        self.assertEqual(self.d_items[0].quantity_delivered, 2)
        self.assertEqual(self.d_items[1].quantity_delivered, 1)

    def test_patch_delivery_invalid_quantity_returns_400(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'items': [
                {'id': self.d_items[0].pk, 'quantity_delivered': 99},
            ],
        }
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_done_success(self):
        self.client.force_authenticate(user=self.user_a)
        for item in self.d_items:
            item.quantity_delivered = item.quantity
            item.save()

        response = self.client.post(self.done_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, Delivery.Status.DONE)
        self.assertEqual(self.delivery.checked_by, self.user_a)

    def test_done_bad_request(self):
        with patch('invensys.views.Delivery.done') as mock_done:
            mock_done.side_effect = ValueError('Stock error')
            self.client.force_authenticate(user=self.user_a)
            response = self.client.post(self.done_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, Delivery.Status.DRAFT)

    def test_cancel_success(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, Delivery.Status.CANCELLED)

    def test_cancel_bad_request(self):
        with patch('invensys.views.Delivery.cancel') as mock_cancel:
            mock_cancel.side_effect = ValueError('Cannot cancel')
            self.client.force_authenticate(user=self.user_a)
            response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, Delivery.Status.DRAFT)


class ReceiptViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user_a = User.objects.create_user(username='usera_rcp', password='password123')

        self.category = Category.objects.create(name='Cat', created_by=self.user_a)
        self.unit = Unit.objects.create(name='pcs')
        self.unit2 = Unit.objects.create(name='box')
        self.product = Product.objects.create(
            name='Item A',
            category=self.category,
            created_by=self.user_a,
            updated_by=self.user_a,
        )
        self.product2 = Product.objects.create(
            name='Item B',
            category=self.category,
            created_by=self.user_a,
            updated_by=self.user_a,
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

        self.supplier = Supplier.objects.create(
            name='Vendor',
            address='Dock 7',
            created_by=self.user_a,
        )
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            created_by=self.user_a,
            updated_by=self.user_a,
        )
        PurchaseOrderItem.objects.create(
            purchase=self.purchase_order,
            product=self.product,
            unit=self.unit,
            quantity=2,
            price=Decimal('15.00'),
        )
        PurchaseOrderItem.objects.create(
            purchase=self.purchase_order,
            product=self.product2,
            unit=self.unit2,
            quantity=3,
            price=Decimal('10.00'),
        )

        future = timezone.now().date() + timedelta(days=7)
        self.purchase_order.arrival_date = future
        self.purchase_order.save()
        self.purchase_order.confirm()

        self.receipt = self.purchase_order.receipts.get()
        self.r_items = list(self.receipt.items.order_by('pk'))

        self.list_url = reverse('receipt-list')
        self.detail_url = reverse('receipt-detail', kwargs={'pk': self.receipt.pk})
        self.done_url = reverse('receipt-done', kwargs={'pk': self.receipt.pk})
        self.cancel_url = reverse('receipt-cancel', kwargs={'pk': self.receipt.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_create_not_allowed(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.list_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_receipts_list(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row['number'], self.receipt.number)
        self.assertEqual(row['purchase_order']['id'], self.purchase_order.pk)

    def test_get_receipt_detail(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['destination'], 'Dock 7')
        self.assertEqual(len(response.data['items']), 2)

    def test_patch_receipt(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'notes': 'Check seals',
            'items': [
                {'id': self.r_items[0].pk, 'quantity_received': 2, 'notes': 'OK'},
                {'id': self.r_items[1].pk, 'quantity_received': 2, 'notes': 'OK'},
            ],
        }
        response = self.client.patch(self.detail_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.r_items[0].refresh_from_db()
        self.r_items[1].refresh_from_db()
        self.assertEqual(self.r_items[0].quantity_received, 2)
        self.assertEqual(self.r_items[1].quantity_received, 2)

    def test_patch_receipt_invalid_quantity_returns_400(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'items': [
                {'id': self.r_items[0].pk, 'quantity_received': 999},
            ],
        }
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_done_success(self):
        self.client.force_authenticate(user=self.user_a)
        for item in self.r_items:
            item.quantity_received = item.quantity
            item.save()

        response = self.client.post(self.done_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.status, Receipt.Status.DONE)
        self.assertEqual(self.receipt.checked_by, self.user_a)

    def test_done_bad_request(self):
        with patch('invensys.views.Receipt.done') as mock_done:
            mock_done.side_effect = ValueError('Cannot complete')
            self.client.force_authenticate(user=self.user_a)
            response = self.client.post(self.done_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.status, Receipt.Status.DRAFT)

    def test_cancel_success(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.status, Receipt.Status.CANCELLED)

    def test_cancel_bad_request(self):
        with patch('invensys.views.Receipt.cancel') as mock_cancel:
            mock_cancel.side_effect = ValueError('Cannot cancel')
            self.client.force_authenticate(user=self.user_a)
            response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.status, Receipt.Status.DRAFT)
