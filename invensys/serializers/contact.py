from rest_framework import serializers
from ..models import Customer, Supplier
from ..constants import METADATA_FIELDS, READ_ONLY_FIELDS


class CustomerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'business_entity', 'phone', 'email', 'address'] + METADATA_FIELDS
        read_only_fields = READ_ONLY_FIELDS


class SupplierDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['name', 'business_entity', 'phone', 'email', 'address'] + METADATA_FIELDS
        read_only_fields = READ_ONLY_FIELDS


class CustomerListSerializer(CustomerDetailSerializer):
    count_sale_orders = serializers.IntegerField(read_only=True)
    last_sale_order_date = serializers.DateTimeField(read_only=True)
    total_sale_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta(CustomerDetailSerializer.Meta):
        fields = CustomerDetailSerializer.Meta.fields + [
            'count_sale_orders', 'last_sale_order_date', 'total_sale_amount'
        ]


class SupplierListSerializer(SupplierDetailSerializer):
    count_purchase_orders = serializers.IntegerField(read_only=True)
    last_purchase_order_date = serializers.DateTimeField(read_only=True)
    total_purchase_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )

    class Meta(SupplierDetailSerializer.Meta):
        fields = SupplierDetailSerializer.Meta.fields + [
            'count_purchase_orders', 'last_purchase_order_date', 'total_purchase_amount'
        ]
