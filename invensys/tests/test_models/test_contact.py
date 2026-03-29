from django.test import TestCase
from invensys.models import Customer, Supplier
from django.core.exceptions import ValidationError


class BaseContactModelTest:
    model = None

    def setUp(self):
        self.contact = self.model.objects.create(
            name='Test Contact',
            business_entity='perorangan',
        )

    def test_total_selection_of_business_entity_is_5(self):
        self.assertEqual(len(self.model.BusinessEntity.choices), 5)

    def test_business_entity_is_set_to_perorangan_by_default(self):
        self.assertEqual(self.contact.business_entity, self.model.BusinessEntity.PERORANGAN)

    def test_error_when_business_entity_is_not_in_choices(self):
        with self.assertRaises(ValidationError):
            self.model.objects.create(name='Test Contact', business_entity='not_in_choices')

    def test_string_representation(self):
        self.assertEqual(str(self.contact), 'Perorangan. Test Contact')


class CustomerModelTest(BaseContactModelTest, TestCase):
    model = Customer


class SupplierModelTest(BaseContactModelTest, TestCase):
    model = Supplier
