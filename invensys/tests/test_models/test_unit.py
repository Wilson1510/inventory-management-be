from django.test import TestCase
from invensys.models import Unit


class UnitModelTest(TestCase):
    def setUp(self):
        self.unit = Unit.objects.create(name='Test Unit')

    def test_string_representation(self):
        self.assertEqual(str(self.unit), 'Test Unit')
