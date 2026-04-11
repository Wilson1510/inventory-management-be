from rest_framework import serializers
from ..models import (
    Customer, Supplier, Product, Unit, 
    SalesOrder, SalesOrderItem, PurchaseOrder, PurchaseOrderItem
)
from .unit import UnitNestedSerializer
from .product import ProductNestedSerializer
from .contact import CustomerNestedSerializer, SupplierNestedSerializer
from .utils import METADATA_FIELDS, READ_ONLY_FIELDS, sync_fk_children
from django.db import transaction


class SalesOrderItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    product = ProductNestedSerializer(read_only=True)
    unit = UnitNestedSerializer(read_only=True)
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), source='unit', write_only=True
    )

    class Meta:
        model = SalesOrderItem
        fields = ['id', 'product_id', 'quantity', 'price', 'unit_id', 'product', 'unit']


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    product = ProductNestedSerializer(read_only=True)
    unit = UnitNestedSerializer(read_only=True)
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), source='unit', write_only=True
    )

    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'product_id', 'quantity', 'price', 'unit_id', 'product', 'unit']


class SalesOrderDetailSerializer(serializers.ModelSerializer):
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), source='customer', write_only=True
    )
    customer = CustomerNestedSerializer(read_only=True)
    items = SalesOrderItemSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = [
            'number', 'status', 'total', 'customer', 'customer_id', 'delivery_date', 'items'
        ] + METADATA_FIELDS
        read_only_fields = ['number', 'status', 'total'] + READ_ONLY_FIELDS

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = SalesOrder.objects.create(**validated_data)

        for item_data in items_data:
            SalesOrderItem.objects.create(sales=order, **item_data)

        order.refresh_from_db()
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if items_data is not None:
                sync_fk_children(
                    instance,
                    items_data,
                    related_name='items',
                    model=SalesOrderItem,
                    fk_field='sales',
                )

        instance.refresh_from_db()
        return instance


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), source='supplier', write_only=True
    )
    supplier = SupplierNestedSerializer(read_only=True)
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'number', 'status', 'total', 'supplier', 'supplier_id', 'arrival_date', 'items'
        ] + METADATA_FIELDS
        read_only_fields = ['number', 'status', 'total'] + READ_ONLY_FIELDS

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = PurchaseOrder.objects.create(**validated_data)

        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase=order, **item_data)

        order.refresh_from_db()
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if items_data is not None:
                sync_fk_children(
                    instance,
                    items_data,
                    related_name='items',
                    model=PurchaseOrderItem,
                    fk_field='purchase',
                )

        instance.refresh_from_db()
        return instance


class SalesOrderListSerializer(serializers.ModelSerializer):
    customer = CustomerNestedSerializer(read_only=True)

    class Meta:
        model = SalesOrder
        fields = ['number', 'status', 'total', 'customer', 'delivery_date'] + METADATA_FIELDS


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    supplier = SupplierNestedSerializer(read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['number', 'status', 'total', 'supplier', 'arrival_date'] + METADATA_FIELDS


class SalesOrderNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = ['id', 'number']


class PurchaseOrderNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ['id', 'number']
