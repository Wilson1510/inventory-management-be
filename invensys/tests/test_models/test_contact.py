from django.test import TestCase
from invensys.models import Customer, Supplier


class BaseContactModelTest:
    model = None

    def setUp(self):
        self.contact = self.model.objects.create(
            name='Test Contact',
            business_entity='perorangan',
        )

    def test_string_representation(self):
        self.assertEqual(str(self.contact), 'Perorangan. Test Contact')


class CustomerModelTest(BaseContactModelTest, TestCase):
    model = Customer


class SupplierModelTest(BaseContactModelTest, TestCase):
    model = Supplier
