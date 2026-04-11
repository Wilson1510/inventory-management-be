from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserViewSetTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
        )
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpass123',
            first_name='Staff',
            last_name='Member',
        )
        self.other = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='Person',
        )
        self.list_url = reverse('user-list')
        self.me_url = reverse('user-me')
        self.detail_other = reverse('user-detail', kwargs={'pk': self.other.pk})
        self.reset_other = reverse('user-reset-password', kwargs={'pk': self.other.pk})
        self.change_password_url = reverse('user-change-password')

    def test_unauthenticated_list_unauthorized(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_list_users_forbidden(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_admin_only(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {row['username'] for row in response.data}
        self.assertIn('admin', usernames)
        self.assertIn('other', usernames)

    def test_list_users_allowed_for_role_admin_without_superuser(self):
        role_admin = User.objects.create_user(
            username='roleadmin',
            email='ra@example.com',
            password='rapass123',
            role=User.Role.ADMIN,
            first_name='Role',
            last_name='Admin',
        )
        self.client.force_authenticate(user=role_admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_retrieve_user_forbidden(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.detail_other)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_user_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.detail_other)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'other')
        self.assertEqual(response.data['name'], 'Other Person')

    def test_me_get_authenticated(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'staff')
        self.assertEqual(response.data['name'], 'Staff Member')
        self.assertEqual(response.data['role'], User.Role.STAFF)

    def test_me_get_unauthenticated_unauthorized(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch_profile(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            self.me_url,
            {'email': 'new@example.com', 'name': 'Updated Name'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertEqual(response.data['name'], 'Updated Name')
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'new@example.com')
        self.assertEqual(self.staff.name, 'Updated Name')

    def test_me_patch_cannot_change_role(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            self.me_url,
            {'role': User.Role.ADMIN},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.role, User.Role.STAFF)

    def test_create_user(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            'username': 'newstaff',
            'email': 'new@example.com',
            'name': 'New Staff',
            'role': User.Role.STAFF,
            'is_active': True,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['name'], 'New Staff')
        created = User.objects.get(username='newstaff')
        self.assertEqual(created.first_name, 'New')
        self.assertEqual(created.last_name, 'Staff')

    def test_create_without_name_bad_request(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            'username': 'noname',
            'role': User.Role.STAFF,
            'is_active': True,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_patch_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            self.detail_other,
            {'name': 'Patched Name'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Patched Name')
        self.other.refresh_from_db()
        self.assertEqual(self.other.name, 'Patched Name')

    def test_delete_user(self):
        to_delete = User.objects.create_user(
            username='todelete',
            password='x',
            first_name='T',
            last_name='D',
        )
        url = reverse('user-detail', kwargs={'pk': to_delete.pk})
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=to_delete.pk).exists())

    def test_reset_password(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            self.reset_other,
            {'new_password': 'resetpass99', 'confirm_password': 'resetpass99'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Password reset successfully')
        self.other.refresh_from_db()
        self.assertTrue(self.other.check_password('resetpass99'))

    def test_reset_password_mismatch(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            self.reset_other,
            {'new_password': 'a', 'confirm_password': 'b'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            self.change_password_url,
            {
                'old_password': 'staffpass123',
                'new_password': 'staffpass999',
                'confirm_password': 'staffpass999',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Password changed successfully')
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password('staffpass999'))

    def test_change_password_wrong_old(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            self.change_password_url,
            {
                'old_password': 'wrong',
                'new_password': 'nope12345',
                'confirm_password': 'nope12345',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
