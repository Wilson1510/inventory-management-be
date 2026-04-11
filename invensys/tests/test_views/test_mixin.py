from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from ...models import Category


class UserTrackingMixinTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')

        self.category = Category.objects.create(name='Elektronik', created_by=self.user_a)

        self.list_url = reverse('category-list')
        self.detail_url = reverse('category-detail', kwargs={'pk': self.category.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_object_sets_tracking_fields(self):
        self.client.force_authenticate(user=self.user_a)
        data = {'name': 'Pakaian'}

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_category = Category.objects.get(name='Pakaian')
        self.assertEqual(new_category.created_by, self.user_a)
        self.assertEqual(new_category.updated_by, self.user_a)

    def test_update_object_changes_only_updated_by(self):
        self.client.force_authenticate(user=self.user_b)
        data = {'name': 'Elektronik Updated'}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Elektronik Updated')
        self.assertEqual(self.category.created_by, self.user_a)
        self.assertEqual(self.category.updated_by, self.user_b)

    def test_update_object_with_metadata(self):
        self.client.force_authenticate(user=self.user_b)

        full_data = {'name': 'Elektronik Full Update', 'created_by': 999}

        response = self.client.put(self.detail_url, full_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()

        self.assertEqual(self.category.name, 'Elektronik Full Update')
        self.assertEqual(self.category.created_by, self.user_a)
        self.assertEqual(self.category.updated_by, self.user_b)
