from django.db import models
from .base import BaseModel
# from .order import SalesOrder, PurchaseOrder
from .product import Product, Unit, ProductUnit
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


class Shipment(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        DONE = 'done', 'Done'
        CANCELLED = 'cancelled', 'Cancelled'

    class ShipmentMethod(models.TextChoices):
        PICKUP = 'pickup', 'Pickup'
        DELIVERY = 'delivery', 'Delivery'

    number = models.CharField(max_length=150, unique=True, null=True, blank=True)
    status = models.CharField(max_length=100, choices=Status.choices, default=Status.DRAFT)
    method = models.CharField(
        max_length=100, choices=ShipmentMethod.choices, default=ShipmentMethod.PICKUP
    )
    notes = models.TextField(null=True, blank=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.number:
            self.number = self._generate_number()
            super().save(update_fields=["number"])

    def _generate_number(self):
        return f"{self.NUMBER_PREFIX}{self.pk:05d}"

    def __str__(self):
        return self.number


class Delivery(Shipment):
    NUMBER_PREFIX = 'DO'

    sales_order = models.ForeignKey(
        'invensys.SalesOrder', on_delete=models.CASCADE, related_name='deliveries'
    )
    delivery_date = models.DateField()

    def done(self, user):
        if user is None:
            raise ValueError("A user must be provided when marking delivery as done")
        with transaction.atomic():
            self.status = self.Status.DONE
            self.checked_by = user
            self.checked_at = timezone.now()
            self._subtract_product_quantity()
            self._adjust_product_base_price_if_stock_is_zero()
            self.save(update_fields=["status", "checked_by", "checked_at"])

    def cancel(self):
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])

    def _subtract_product_quantity(self):
        for item in self.items.all():
            multiplier = item.get_multiplier()
            item.validate_quantity_delivered_less_than_or_equal_to_quantity()
            item.validate_stock_is_available()
            item.product.quantity -= item.quantity_delivered * multiplier
            item.product.save(update_fields=["quantity"])

    def _adjust_product_base_price_if_stock_is_zero(self):
        for item in self.items.all():
            if item.product.quantity == 0:
                item.product.base_price = 0
                item.product.save(update_fields=["base_price"])


class Receipt(Shipment):
    NUMBER_PREFIX = 'RI'

    purchase_order = models.ForeignKey(
        'invensys.PurchaseOrder', on_delete=models.CASCADE, related_name='receipts'
    )
    arrival_date = models.DateField()

    def done(self, user):
        if user is None:
            raise ValueError("A user must be provided when marking receipt as done")
        with transaction.atomic():
            self.status = self.Status.DONE
            self.checked_by = user
            self.checked_at = timezone.now()
            self._add_product_quantity()
            self._adjust_product_base_price()
            self.save(update_fields=["status", "checked_by", "checked_at"])

    def cancel(self):
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])

    def _add_product_quantity(self):
        for item in self.items.all():
            multiplier = item.get_multiplier()
            item.product.quantity += item.quantity_received * multiplier
            item.product.save(update_fields=["quantity"])

    def _adjust_product_base_price(self):
        for item in self.items.all():
            item.product.base_price = item.calculate_product_base_price()
            item.product.save(update_fields=["base_price"])


class ShipmentItem(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='%(class)s_items')
    quantity = models.IntegerField(default=1)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def get_multiplier(self):
        prod_unit = ProductUnit.objects.get(product=self.product, unit=self.unit)
        return prod_unit.multiplier


class DeliveryItem(ShipmentItem):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='items')
    quantity_delivered = models.IntegerField(default=0)

    def validate_quantity_delivered_less_than_or_equal_to_quantity(self):
        if self.quantity_delivered > self.quantity:
            raise ValueError("Quantity delivered must be less than or equal to quantity")

    def validate_stock_is_available(self):
        if self.quantity_delivered > self.product.quantity:
            raise ValueError(f"Stock is not available for product {self.product.name}")

    def __str__(self):
        return f"{self.delivery.number} - {self.product.name}"


class ReceiptItem(ShipmentItem):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='items')
    quantity_received = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def calculate_product_base_price(self):
        multiplier = self.get_multiplier()

        incoming_qty = self.quantity_received * multiplier
        price_per_base_unit = Decimal(self.price) / Decimal(multiplier)
        incoming_total_value = incoming_qty * price_per_base_unit

        old_qty = self.product.quantity - incoming_qty
        old_base_price = self.product.base_price
        old_total_value = Decimal(old_qty) * Decimal(old_base_price)

        new_total_qty = old_qty + incoming_qty
        new_total_value = old_total_value + incoming_total_value
        new_base_price = new_total_value / Decimal(new_total_qty)

        new_base_price = new_base_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return new_base_price

    def __str__(self):
        return f"{self.receipt.number} - {self.product.name}"
