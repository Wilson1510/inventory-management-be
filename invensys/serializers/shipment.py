from rest_framework import serializers
from django.db import transaction
from ..models import Delivery, DeliveryItem, Receipt, ReceiptItem
from .unit import UnitNestedSerializer
from .product import ProductNestedSerializer
from .order import SalesOrderNestedSerializer, PurchaseOrderNestedSerializer
from .utils import METADATA_FIELDS, READ_ONLY_FIELDS


class DeliveryItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product = ProductNestedSerializer(read_only=True)
    unit = UnitNestedSerializer(read_only=True)

    class Meta:
        model = DeliveryItem
        fields = ['id', 'product', 'quantity', 'quantity_delivered', 'unit', 'notes']
        read_only_fields = ['product', 'quantity', 'unit']


class ReceiptItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    product = ProductNestedSerializer(read_only=True)
    unit = UnitNestedSerializer(read_only=True)

    class Meta:
        model = ReceiptItem
        fields = ['id', 'product', 'quantity', 'quantity_received', 'unit', 'notes', 'price']
        read_only_fields = ['product', 'quantity', 'unit', 'price']


class DeliveryDetailSerializer(serializers.ModelSerializer):
    sales_order = SalesOrderNestedSerializer(read_only=True)
    items = DeliveryItemSerializer(many=True)
    destination = serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = [
            'number', 'status', 'method', 'sales_order', 'delivery_date', 'notes', 'checked_by',
            'checked_at', 'destination', 'items'
        ] + METADATA_FIELDS
        read_only_fields = [
            'number', 'status', 'sales_order', 'delivery_date', 'checked_by',
            'checked_at', 'destination',
        ] + READ_ONLY_FIELDS

    def get_destination(self, obj):
        customer = getattr(obj.sales_order, 'customer', None)
        return customer.address if customer and customer.address else None

    def validate(self, attrs):
        items_data = attrs.get('items')
        if items_data is not None and self.instance is not None:
            for row in items_data:
                pk = row.get('id')
                self._check_pk_exists_in_items(pk)
                item = self._check_item_object_exists_and_get_it(pk)
                self._validate_quantity_delivered(item, row)
        return attrs

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if items_data is not None:
                for row in items_data:
                    self._update_delivery_item(instance, row)

        instance.refresh_from_db()
        return instance

    def _check_pk_exists_in_items(self, pk):
        if pk is None:
            raise serializers.ValidationError({'items': 'Each item must include id'})

    def _check_item_object_exists_and_get_it(self, pk):
        try:
            item = self.instance.items.get(pk=pk)
        except DeliveryItem.DoesNotExist:
            raise serializers.ValidationError({'items': f'Invalid item id: {pk}'})
        return item

    def _validate_quantity_delivered(self, item, row):
        qd = row.get('quantity_delivered', item.quantity_delivered)
        if qd > item.quantity:
            raise serializers.ValidationError(
                {'items': 'Quantity delivered must be less than or equal to quantity'}
            )

    def _update_delivery_item(self, instance, row):
        pk = row['id']
        item = instance.items.get(pk=pk)
        payload = {k: v for k, v in row.items() if k != 'id'}
        child_serializer = DeliveryItemSerializer(
            item, data=payload, partial=True
        )
        child_serializer.is_valid(raise_exception=True)
        child_serializer.save()


class ReceiptDetailSerializer(serializers.ModelSerializer):
    purchase_order = PurchaseOrderNestedSerializer(read_only=True)
    items = ReceiptItemSerializer(many=True)
    destination = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = [
            'number', 'status', 'method', 'purchase_order', 'arrival_date', 'notes', 'checked_by',
            'checked_at', 'destination', 'items'
        ] + METADATA_FIELDS
        read_only_fields = [
            'number', 'status', 'purchase_order', 'arrival_date', 'checked_by',
            'checked_at', 'destination'
        ] + READ_ONLY_FIELDS

    def get_destination(self, obj):
        supplier = getattr(obj.purchase_order, 'supplier', None)
        return supplier.address if supplier and supplier.address else None

    def validate(self, attrs):
        items_data = attrs.get('items')
        if items_data is not None and self.instance is not None:
            for row in items_data:
                pk = row.get('id')
                self._check_pk_exists_in_items(pk)
                item = self._check_item_object_exists_and_get_it(pk)
                self._validate_quantity_received(item, row)
        return attrs

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if items_data is not None:
                for row in items_data:
                    self._update_receipt_item(instance, row)

        instance.refresh_from_db()
        return instance

    def _check_pk_exists_in_items(self, pk):
        if pk is None:
            raise serializers.ValidationError({'items': 'Each item must include id'})

    def _check_item_object_exists_and_get_it(self, pk):
        try:
            item = self.instance.items.get(pk=pk)
        except ReceiptItem.DoesNotExist:
            raise serializers.ValidationError({'items': f'Invalid item id: {pk}'})
        return item

    def _validate_quantity_received(self, item, row):
        qr = row.get('quantity_received', item.quantity_received)
        if qr > item.quantity:
            raise serializers.ValidationError(
                {'items': 'Quantity received must be less than or equal to quantity'}
            )

    def _update_receipt_item(self, instance, row):
        pk = row['id']
        item = instance.items.get(pk=pk)
        payload = {k: v for k, v in row.items() if k != 'id'}
        child_serializer = ReceiptItemSerializer(
            item, data=payload, partial=True
        )
        child_serializer.is_valid(raise_exception=True)
        child_serializer.save()


class DeliveryListSerializer(serializers.ModelSerializer):
    sales_order = SalesOrderNestedSerializer(read_only=True)

    class Meta:
        model = Delivery
        fields = ['number', 'status', 'method', 'sales_order', 'delivery_date'] + METADATA_FIELDS


class ReceiptListSerializer(serializers.ModelSerializer):
    purchase_order = PurchaseOrderNestedSerializer(read_only=True)

    class Meta:
        model = Receipt
        fields = ['number', 'status', 'method', 'purchase_order', 'arrival_date'] + METADATA_FIELDS
