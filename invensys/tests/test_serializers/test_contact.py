from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from ...models import Customer, Supplier
from ...serializers import CustomerListSerializer, SupplierListSerializer


class CustomerSerializerTests(TestCase):
    def setUp(self):
        self.existing_customer = Customer.objects.create(
            name="Existing Customer",
            business_entity=Customer.BusinessEntity.PT,
            phone="08123456789",
            email="existing@test.com",
            address="Jl. Lama No 1"
        )

    def test_list_serializer_reads_annotated_fields(self):
        dummy_date = timezone.now()

        self.existing_customer.count_sale_orders = 5
        self.existing_customer.total_sale_amount = Decimal("1500000.00")
        self.existing_customer.last_sale_order_date = dummy_date

        serializer = CustomerListSerializer(instance=self.existing_customer)
        data = serializer.data

        self.assertEqual(data['count_sale_orders'], 5)
        self.assertEqual(data['total_sale_amount'], "1500000.00")
        self.assertEqual(data['name'], "Existing Customer")


class SupplierSerializerTests(TestCase):
    def setUp(self):
        self.existing_supplier = Supplier.objects.create(
            name="Existing Supplier",
            business_entity=Supplier.BusinessEntity.PT,
            phone="08123456789",
            email="existing@test.com",
            address="Jl. Lama No 1"
        )

    def test_list_serializer_reads_annotated_fields(self):
        dummy_date = timezone.now()

        self.existing_supplier.count_purchase_orders = 5
        self.existing_supplier.total_purchase_amount = Decimal("1500000.00")
        self.existing_supplier.last_purchase_order_date = dummy_date

        serializer = SupplierListSerializer(instance=self.existing_supplier)
        data = serializer.data

        self.assertEqual(data['count_purchase_orders'], 5)
        self.assertEqual(data['total_purchase_amount'], "1500000.00")
        self.assertEqual(data['name'], "Existing Supplier")
