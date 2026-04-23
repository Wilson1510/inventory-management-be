from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ...models import Category, Product


class CategoryViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='admin', password='password123')
        self.category = Category.objects.create(name='Elektronik')

        self.list_url = reverse('category-list')
        self.detail_url = reverse('category-detail', kwargs={'pk': self.category.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_access_denied(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='password123')
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_categories_list(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.category.name)

    def test_get_category_detail(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.category.name)

    def test_create_category(self):
        self.client.force_authenticate(user=self.admin)
        data = {'name': 'Pakaian'}

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_category = Category.objects.get(name='Pakaian')
        self.assertEqual(new_category.name, 'Pakaian')

    def test_update_category(self):
        self.client.force_authenticate(user=self.admin)
        data = {'name': 'Elektronik Updated'}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Elektronik Updated')

    def test_delete_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_delete_category_blocked_when_has_products(self):
        Product.objects.create(
            name='Linked Product',
            category=self.category,
            created_by=self.admin,
            updated_by=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['code'], 'category_has_products')
        self.assertIn('detail', response.data)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
