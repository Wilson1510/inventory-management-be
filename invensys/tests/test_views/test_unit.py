from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ...models import Category, Customer, Product, ProductUnit, SalesOrder, SalesOrderItem, Unit


class UnitViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='admin', password='password123')
        self.unit = Unit.objects.create(name='Pcs')

        self.list_url = reverse('unit-list')
        self.detail_url = reverse('unit-detail', kwargs={'pk': self.unit.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_access_denied(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='password123')
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_units_list(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.unit.name)

    def test_get_unit_detail(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.unit.name)

    def test_create_unit(self):
        self.client.force_authenticate(user=self.admin)
        data = {'name': 'Box'}

        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_unit = Unit.objects.get(name='Box')
        self.assertEqual(new_unit.name, 'Box')

    def test_update_unit(self):
        self.client.force_authenticate(user=self.admin)
        data = {'name': 'Pcs Updated'}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.unit.refresh_from_db()
        self.assertEqual(self.unit.name, 'Pcs Updated')

    def test_delete_unit(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Unit.objects.filter(pk=self.unit.pk).exists())

    def test_delete_unit_blocked_when_referenced_by_order_item(self):
        cat = Category.objects.create(name='CatRef')
        prod = Product.objects.create(
            name='ProdRef',
            category=cat,
            created_by=self.admin,
            updated_by=self.admin,
        )
        ProductUnit.objects.create(
            product=prod,
            unit=self.unit,
            multiplier=1,
            is_base_unit=True,
        )
        cust = Customer.objects.create(name='Buyer', created_by=self.admin)
        so = SalesOrder.objects.create(
            customer=cust,
            created_by=self.admin,
            updated_by=self.admin,
        )
        SalesOrderItem.objects.create(
            sales=so,
            product=prod,
            unit=self.unit,
            quantity=1,
            price=Decimal('10.00'),
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['code'], 'unit_has_references')
        self.assertIn('detail', response.data)
        self.assertTrue(Unit.objects.filter(pk=self.unit.pk).exists())
