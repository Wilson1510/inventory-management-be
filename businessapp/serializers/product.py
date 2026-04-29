from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException
from ..models import Product, ProductPrice, ProductUnit, Unit, Category
from .unit import UnitNestedSerializer
from .category import CategoryNestedSerializer
from .utils import METADATA_FIELDS, READ_ONLY_FIELDS, sync_fk_children

class DuplicatePayloadError(APIException):
    status_code = 400
    default_code = 'invalid'

    def __init__(self, detail, code=None):
        self.detail = {'detail': detail, 'code': code or self.default_code}


class ProductPriceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), source='unit', write_only=True
    )
    unit = UnitNestedSerializer(read_only=True)

    class Meta:
        model = ProductPrice
        fields = ['id', 'price', 'minimum_quantity', 'unit_id', 'unit']


class ProductUnitSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), source='unit', write_only=True
    )
    unit = UnitNestedSerializer(read_only=True)

    class Meta:
        model = ProductUnit
        fields = ['id', 'unit_id', 'multiplier', 'is_base_unit', 'unit']


class ProductDetailSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    category = CategoryNestedSerializer(read_only=True)

    prices = ProductPriceSerializer(many=True)
    units = ProductUnitSerializer(many=True, source='productunit_set')

    class Meta:
        model = Product
        fields = [
            'name', 'sku_number', 'category', 'category_id', 'base_price', 'prices', 'quantity',
            'units'
        ] + METADATA_FIELDS
        read_only_fields = [
            'sku_number', 'base_price', 'quantity'
        ] + READ_ONLY_FIELDS

    def validate(self, attrs):
        units_data = attrs.get('productunit_set')
        if units_data is not None:
            seen_units = set()
            for i, unit_data in enumerate(units_data):
                unit = unit_data.get('unit')
                if unit:
                    if unit.id in seen_units:
                        raise DuplicatePayloadError(
                            "Duplicate units are not allowed.",
                            code="duplicate_unit_in_payload"
                        )
                    seen_units.add(unit.id)

        prices_data = attrs.get('prices')
        if prices_data is not None:
            seen_prices = set()
            for price_data in prices_data:
                unit = price_data.get('unit')
                min_qty = price_data.get('minimum_quantity')
                if unit and min_qty is not None:
                    key = (unit.id, min_qty)
                    if key in seen_prices:
                        raise DuplicatePayloadError(
                            "Duplicate prices for the same unit and minimum quantity are not allowed.",
                            code="duplicate_price_in_payload"
                        )
                    seen_prices.add(key)

        return attrs

    def create(self, validated_data):
        prices_data = validated_data.pop('prices', [])
        units_data = validated_data.pop('productunit_set', [])
        user = self.context['request'].user if 'request' in self.context else None

        with transaction.atomic():
            product = Product.objects.create(**validated_data)

            price_objs = []
            for price_data in prices_data:
                kwargs = {'product': product, **price_data}
                if user:
                    kwargs['created_by'] = user
                    kwargs['updated_by'] = user
                price_objs.append(ProductPrice(**kwargs))
            ProductPrice.objects.bulk_create(price_objs)

            unit_objs = []
            for unit_data in units_data:
                kwargs = {'product': product, **unit_data}
                if user:
                    kwargs['created_by'] = user
                    kwargs['updated_by'] = user
                unit_objs.append(ProductUnit(**kwargs))
            ProductUnit.objects.bulk_create(unit_objs)

        return product

    def update(self, instance, validated_data):
        prices_data = validated_data.pop('prices', None)
        units_data = validated_data.pop('productunit_set', None)
        user = self.context['request'].user if 'request' in self.context else None

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if prices_data is not None:
                sync_fk_children(
                    instance,
                    prices_data,
                    related_name='prices',
                    model=ProductPrice,
                    fk_field='product',
                    user=user,
                )
            if units_data is not None:
                sync_fk_children(
                    instance,
                    units_data,
                    related_name='productunit_set',
                    model=ProductUnit,
                    fk_field='product',
                    user=user,
                )

        return instance


class ProductListSerializer(serializers.ModelSerializer):
    category = CategoryNestedSerializer(read_only=True)
    price = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'name', 'sku_number', 'category', 'base_price', 'price', 'quantity', 'unit'
        ] + METADATA_FIELDS

    def get_unit(self, obj):
        base_product_unit = obj.productunit_set.filter(is_base_unit=True).first()
        if base_product_unit:
            return base_product_unit.unit.name
        return None

    def get_price(self, obj):
        base_product_unit = obj.productunit_set.filter(is_base_unit=True).first()
        if base_product_unit:
            price_obj = obj.prices.filter(unit=base_product_unit.unit, minimum_quantity=1).first()
            if price_obj:
                return price_obj.price
        return None


class ProductNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name']
