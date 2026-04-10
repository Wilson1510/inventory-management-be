from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user_defaults_role_staff(self):
        user = User.objects.create_user(
            username='staff1', email='staff1@example.com', password='secret'
        )
        self.assertEqual(user.role, User.Role.STAFF)
        self.assertFalse(user.is_superuser)

    def test_create_user_respects_explicit_role(self):
        user = User.objects.create_user(
            username='mgr',
            email='mgr@example.com',
            password='secret',
            role=User.Role.ADMIN,
        )
        self.assertEqual(user.role, User.Role.ADMIN)

    def test_create_superuser_defaults_role_admin(self):
        user = User.objects.create_superuser(
            username='admin1', email='admin1@example.com', password='secret'
        )
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_superuser_respects_explicit_role(self):
        user = User.objects.create_superuser(
            username='superstaff',
            email='superstaff@example.com',
            password='secret',
            role=User.Role.STAFF,
        )
        self.assertEqual(user.role, User.Role.STAFF)

    def test_db_table(self):
        self.assertEqual(User._meta.db_table, 'invensys_user')

    def test_name_property_empty_when_no_first_or_last(self):
        user = User(username='u1', first_name='', last_name='')
        self.assertEqual(user.name, '')

    def test_name_property_first_name_only(self):
        user = User(username='u1', first_name='Ada', last_name='')
        self.assertEqual(user.name, 'Ada')

    def test_name_property_last_name_only(self):
        user = User(username='u1', first_name='', last_name='Lovelace')
        self.assertEqual(user.name, 'Lovelace')

    def test_name_property_joins_first_and_last(self):
        user = User(username='u1', first_name='Ada', last_name='Lovelace')
        self.assertEqual(user.name, 'Ada Lovelace')
