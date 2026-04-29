from invensys.models import Customer
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ...models import Category, Unit, Product, SalesOrder, Customer


class IntegrityErrorSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='admin', password='password123')
        self.category = Category.objects.create(name='Elektronik')
        self.unit = Unit.objects.create(name='pcs')

        self.category_detail_url = reverse('category-detail', kwargs={'pk': self.category.pk})

    def test_create_unit_with_duplicate_name_fail(self):
        self.client.force_authenticate(user=self.admin)
        data = {'name': 'pcs'}
        response = self.client.post(reverse('unit-list'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'unique')
        self.assertIn('detail', response.data)

    def test_create_category_with_duplicate_name_fail_due_to_slug_constraint(self):
        self.client.force_authenticate(user=self.admin)
        data = {'name': 'Elektronik'}
        response = self.client.post(reverse('category-list'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'unique')
        self.assertIn('detail', response.data)


class ProtectedErrorSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='admin', password='password123')
        self.category = Category.objects.create(name='Elektronik')
        self.product = Product.objects.create(name='Product', category=self.category)

        self.category_detail_url = reverse('category-detail', kwargs={'pk': self.category.pk})

    def test_delete_category_blocked_when_has_products(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.category_detail_url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['code'], 'has_references')
        self.assertIn('detail', response.data)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())


class ValueErrorSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='admin', password='password123')
        self.customer = Customer.objects.create(
            name='Customer',
            email='customer@gmail.com',
            phone='08123456789',
            address='Address',
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.sales_order = SalesOrder.objects.create(customer=self.customer, created_by=self.admin, updated_by=self.admin)
        self.sales_order.status = 'confirmed'
        self.sales_order.save()

        self.sales_order_detail_url = reverse('salesorder-detail', kwargs={'pk': self.sales_order.pk})

    def test_delete_sales_order_blocked_when_confirmed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.sales_order_detail_url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['code'], 'confirmed_order')
        self.assertIn('detail', response.data)
        self.assertTrue(SalesOrder.objects.filter(pk=self.sales_order.pk).exists())