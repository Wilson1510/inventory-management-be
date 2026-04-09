from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ...models import Category


class CategoryViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='user', password='password123')
        self.category = Category.objects.create(name='Elektronik')

        self.list_url = reverse('category-list')
        self.detail_url = reverse('category-detail', kwargs={'pk': self.category.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_categories_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.category.name)

    def test_get_category_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.category.name)

    def test_create_category(self):
        self.client.force_authenticate(user=self.user)
        data = {'name': 'Pakaian'}

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_category = Category.objects.get(name='Pakaian')
        self.assertEqual(new_category.name, 'Pakaian')

    def test_update_category(self):
        self.client.force_authenticate(user=self.user)
        data = {'name': 'Elektronik Updated'}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Elektronik Updated')

    def test_delete_category(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())
