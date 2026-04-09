from django.db import transaction
from rest_framework import serializers
from ..models import Product, ProductPrice, ProductUnit, Unit, Category
from .unit import UnitNestedSerializer
from .category import CategoryNestedSerializer
from ..constants import METADATA_FIELDS, READ_ONLY_FIELDS


class ProductPriceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), source='unit', write_only=True
    )

    class Meta:
        model = ProductPrice
        fields = ['id', 'price', 'minimum_quantity', 'unit_id']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['unit'] = UnitNestedSerializer(instance.unit).data
        return rep


class ProductUnitSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), source='unit', write_only=True
    )

    class Meta:
        model = ProductUnit
        fields = ['id', 'unit_id', 'multiplier', 'is_base_unit']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['unit'] = UnitNestedSerializer(instance.unit).data
        return rep


def _sync_fk_children(parent, rows, *, related_name, model, fk_field='product'):
    manager = getattr(parent, related_name)
    existing = {obj.id: obj for obj in manager.all()}
    keep_ids = {row['id'] for row in rows if row.get('id') is not None}

    for pk in existing.keys() - keep_ids:
        existing[pk].delete()

    for row in rows:
        pk = row.get('id')
        payload = {k: v for k, v in row.items() if k != 'id'}
        if pk is not None and pk in existing:
            obj = existing[pk]
            for attr, value in payload.items():
                setattr(obj, attr, value)
            obj.save()
        else:
            model.objects.create(**{fk_field: parent}, **payload)


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

    def create(self, validated_data):
        prices_data = validated_data.pop('prices', [])
        units_data = validated_data.pop('productunit_set', [])

        with transaction.atomic():
            product = Product.objects.create(**validated_data)

            ProductPrice.objects.bulk_create([
                ProductPrice(product=product, **price_data) for price_data in prices_data
            ])

            ProductUnit.objects.bulk_create([
                ProductUnit(product=product, **unit_data) for unit_data in units_data
            ])

        return product

    def update(self, instance, validated_data):
        prices_data = validated_data.pop('prices', None)
        units_data = validated_data.pop('productunit_set', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if prices_data is not None:
                _sync_fk_children(
                    instance,
                    prices_data,
                    related_name='prices',
                    model=ProductPrice,
                )
            if units_data is not None:
                _sync_fk_children(
                    instance,
                    units_data,
                    related_name='productunit_set',
                    model=ProductUnit,
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
