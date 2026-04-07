from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'staff')
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STAFF = 'staff', 'Staff'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF,
    )

    objects = UserManager()

    class Meta:
        db_table = 'invensys_user'
