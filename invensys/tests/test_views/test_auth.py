from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthJWTTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='staffer',
            email='staffer@example.com',
            password='secret12345',
            first_name='Staff',
            last_name='User',
        )
        self.login_url = reverse('auth-login')
        self.refresh_url = reverse('auth-refresh')

    def test_login_returns_tokens_and_user(self):
        response = self.client.post(
            self.login_url,
            {'username': 'staffer', 'password': 'secret12345'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {'username': 'staffer', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_returns_new_access(self):
        login = self.client.post(
            self.login_url,
            {'username': 'staffer', 'password': 'secret12345'},
            format='json',
        )
        refresh = login.data['refresh']
        response = self.client.post(
            self.refresh_url, {'refresh': refresh}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_protected_endpoint_accepts_bearer_token(self):
        login = self.client.post(
            self.login_url,
            {'username': 'staffer', 'password': 'secret12345'},
            format='json',
        )
        token = login.data['access']
        me_url = reverse('user-me')
        response = self.client.get(
            me_url, HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'staffer')
