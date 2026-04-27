from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ...models import Category, Unit, Product


class ExceptionSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='admin', password='password123')
        self.category = Category.objects.create(name='Elektronik')
        self.unit = Unit.objects.create(name='pcs')
        self.product = Product.objects.create(name='Product', category=self.category)

        self.category_detail_url = reverse('category-detail', kwargs={'pk': self.category.pk})

    def test_delete_category_blocked_when_has_products(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.category_detail_url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['code'], 'has_references')
        self.assertIn('detail', response.data)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

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

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['code'], 'unique')
        self.assertIn('detail', response.data)
