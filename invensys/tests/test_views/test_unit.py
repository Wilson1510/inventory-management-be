from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from ...models import Unit


class UnitViewSetTest(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')

        self.unit = Unit.objects.create(name='Pcs', created_by=self.user_a)

        self.list_url = reverse('unit-list')
        self.detail_url = reverse('unit-detail', kwargs={'pk': self.unit.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_units_list(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.unit.name)

    def test_get_unit_detail(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.unit.name)

    def test_create_unit_sets_tracking_fields(self):
        self.client.force_authenticate(user=self.user_a)
        data = {'name': 'Box'}

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_unit = Unit.objects.get(name='Box')
        self.assertEqual(new_unit.created_by, self.user_a)
        self.assertEqual(new_unit.updated_by, self.user_a)

    def test_update_unit_changes_only_updated_by(self):
        self.client.force_authenticate(user=self.user_b)
        data = {'name': 'Pcs Updated'}

        response = self.client.patch(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.unit.refresh_from_db()
        self.assertEqual(self.unit.name, 'Pcs Updated')
        self.assertEqual(self.unit.created_by, self.user_a)
        self.assertEqual(self.unit.updated_by, self.user_b)

    def test_update_unit_with_metadata(self):
        self.client.force_authenticate(user=self.user_b)

        full_data = {'name': 'Pcs Full Update', 'created_by': 999}

        response = self.client.put(self.detail_url, full_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unit.refresh_from_db()

        self.assertEqual(self.unit.name, 'Pcs Full Update')
        self.assertEqual(self.unit.created_by, self.user_a)
        self.assertEqual(self.unit.updated_by, self.user_b)

    def test_delete_unit(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Unit.objects.filter(pk=self.unit.pk).exists())

    def test_create_invalid_unit(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.list_url, {'name': ''})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
