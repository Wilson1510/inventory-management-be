from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from ...serializers.user import (
    UserSerializer, UserPasswordResetSerializer, UserChangePasswordSerializer, UserMeSerializer
)

User = get_user_model()


class UserSerializerTest(TestCase):
    def test_create_requires_name(self):
        serializer = UserSerializer(
            data={
                'username': 'newuser',
                'email': 'n@example.com',
                'role': User.Role.STAFF,
                'is_active': True,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_create_rejects_blank_name(self):
        serializer = UserSerializer(
            data={
                'username': 'newuser',
                'name': '   ',
                'role': User.Role.STAFF,
                'is_active': True,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_create_splits_full_name_into_first_and_last(self):
        serializer = UserSerializer(
            data={
                'username': 'newuser',
                'name': 'Ada Lovelace',
                'role': User.Role.STAFF,
                'is_active': True,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.first_name, 'Ada')
        self.assertEqual(user.last_name, 'Lovelace')
        self.assertEqual(user.name, 'Ada Lovelace')

    def test_create_single_token_name_sets_first_name_only(self):
        serializer = UserSerializer(
            data={
                'username': 'solo',
                'name': 'Madonna',
                'role': User.Role.STAFF,
                'is_active': True,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.first_name, 'Madonna')
        self.assertEqual(user.last_name, '')

    def test_partial_update_without_name_preserves_display_name(self):
        user = User.objects.create_user(
            username='keepname',
            password='secret',
            first_name='Original',
            last_name='User',
        )
        serializer = UserSerializer(
            instance=user,
            data={'is_active': False},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        user.refresh_from_db()
        self.assertEqual(user.name, 'Original User')

    def test_partial_update_with_blank_name_fails(self):
        user = User.objects.create_user(
            username='u',
            password='secret',
            first_name='X',
            last_name='Y',
        )
        serializer = UserSerializer(
            instance=user,
            data={'name': ''},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_update_changes_display_name(self):
        user = User.objects.create_user(
            username='chg',
            password='secret',
            first_name='Old',
            last_name='Name',
        )
        serializer = UserSerializer(
            instance=user,
            data={
                'username': 'chg',
                'email': user.email or '',
                'name': 'New Person',
                'role': user.role,
                'is_active': user.is_active,
            },
            partial=False,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        user.refresh_from_db()
        self.assertEqual(user.name, 'New Person')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'Person')


class UserPasswordResetSerializerTest(TestCase):
    def test_mismatch_confirm_fails(self):
        serializer = UserPasswordResetSerializer(
            data={'new_password': 'a', 'confirm_password': 'b'}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)

    def test_matching_passwords_valid(self):
        serializer = UserPasswordResetSerializer(
            data={'new_password': 'newsecret123', 'confirm_password': 'newsecret123'}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class UserChangePasswordSerializerTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='me',
            email='me@example.com',
            password='oldpass123',
        )

    def test_wrong_old_password_fails(self):
        request = self.factory.post('/')
        request.user = self.user
        serializer = UserChangePasswordSerializer(
            data={
                'old_password': 'wrong',
                'new_password': 'newpass123',
                'confirm_password': 'newpass123',
            },
            context={'request': request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)

    def test_mismatch_new_and_confirm_fails(self):
        request = self.factory.post('/')
        request.user = self.user
        serializer = UserChangePasswordSerializer(
            data={
                'old_password': 'oldpass123',
                'new_password': 'aaa',
                'confirm_password': 'bbb',
            },
            context={'request': request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)

    def test_valid_change_password(self):
        request = self.factory.post('/')
        request.user = self.user
        serializer = UserChangePasswordSerializer(
            data={
                'old_password': 'oldpass123',
                'new_password': 'newpass456',
                'confirm_password': 'newpass456',
            },
            context={'request': request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class UserMeSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='meuser',
            email='me@example.com',
            password='secret',
            first_name='Me',
            last_name='User',
        )

    def test_patch_name_and_email(self):
        serializer = UserMeSerializer(
            self.user,
            data={'email': 'x@example.com', 'name': 'New Full Name'},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'x@example.com')
        self.assertEqual(self.user.name, 'New Full Name')

    def test_patch_blank_name_invalid(self):
        serializer = UserMeSerializer(
            self.user,
            data={'name': ''},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_patch_blank_email_valid(self):
        serializer = UserMeSerializer(
            self.user,
            data={'email': ''},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, '')

    def test_patch_ignores_role_in_input(self):
        serializer = UserMeSerializer(
            self.user,
            data={'role': User.Role.ADMIN},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.STAFF)
