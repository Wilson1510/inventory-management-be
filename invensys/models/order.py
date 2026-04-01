from django.db import models
from .base import BaseModel
from .contact import Customer, Supplier
from .product import Product, Unit, ProductUnit
from django.db.models import Sum, F
from django.db import transaction
from django.apps import apps
from django.utils import timezone


class BaseOrder(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    number = models.CharField(max_length=150, unique=True, null=True, blank=True)
    status = models.CharField(max_length=100, choices=Status.choices, default=Status.DRAFT)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.number:
            self.number = self._generate_number()
            super().save(update_fields=["number"])

    def calculate_total(self):
        return self.items.aggregate(total=Sum(F("price") * F("quantity")))["total"] or 0

    def update_total(self):
        self.total = self.calculate_total()
        self.save(update_fields=["total"])

    def _generate_number(self):
        return f"{self.__class__.__name__[0].upper()}{self.pk:05d}"

    def _validate_items_exist(self):
        if not self.items.exists():
            raise ValueError("Add items to the order before confirming")

    def _validate_items_quantities(self):
        for item in self.items.all():
            if item.quantity <= 0:
                raise ValueError("Quantity of each item must be greater than zero")

    def __str__(self):
        return self.number


class PurchaseOrder(BaseOrder):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='purchase_orders'
    )
    arrival_date = models.DateField(null=True, blank=True)

    def confirm(self):
        self._validate_purchase_order_before_confirming()
        with transaction.atomic():
            self.status = self.Status.CONFIRMED
            self.save(update_fields=["status"])
            self._create_receipt_order_and_items()

    def _validate_purchase_order_before_confirming(self):
        self._validate_items_exist()
        self._validate_items_quantities()
        self._validate_arrival_date_exists()
        self._validate_arrival_date_is_in_the_future()

    def _validate_arrival_date_exists(self):
        if self.arrival_date is None:
            raise ValueError("Arrival date must be set")

    def _validate_arrival_date_is_in_the_future(self):
        if self.arrival_date <= timezone.now().date():
            raise ValueError("Arrival date must be in the future")

    def cancel(self):
        with transaction.atomic():
            self._cancel_receipts()
            self.status = self.Status.CANCELLED
            self.save(update_fields=["status"])

    def _cancel_receipts(self):
        for receipt in self.receipts.all():
            if receipt.status == receipt.Status.DONE:
                raise ValueError("Receipt cannot be cancelled if it is done")
            receipt.cancel()

    def _create_receipt_order_and_items(self):
        Receipt = apps.get_model('invensys', 'Receipt')
        receipt = Receipt.objects.create(
            purchase_order=self,
            arrival_date=self.arrival_date
        )
        ReceiptItem = apps.get_model('invensys', 'ReceiptItem')
        for item in self.items.all():
            ReceiptItem.objects.create(
                receipt=receipt,
                product=item.product,
                quantity=item.quantity,
                unit=item.unit,
                price=item.price
            )


class SalesOrder(BaseOrder):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='sales_orders'
    )
    delivery_date = models.DateField(null=True, blank=True)

    def confirm(self):
        self._validate_sales_order_before_confirming()
        with transaction.atomic():
            self.status = self.Status.CONFIRMED
            self.save(update_fields=["status"])
            self._create_delivery_order_and_items()

    def cancel(self):
        with transaction.atomic():
            self._cancel_deliveries()
            self.status = self.Status.CANCELLED
            self.save(update_fields=["status"])

    def _validate_sales_order_before_confirming(self):
        self._validate_items_exist()
        self._validate_items_quantities()
        self._validate_delivery_date_exists()
        self._validate_delivery_date_is_in_the_future()

    def _validate_delivery_date_exists(self):
        if self.delivery_date is None:
            raise ValueError("Delivery date must be set")

    def _validate_delivery_date_is_in_the_future(self):
        if self.delivery_date <= timezone.now().date():
            raise ValueError("Delivery date must be in the future")

    def _cancel_deliveries(self):
        for delivery in self.deliveries.all():
            if delivery.status == delivery.Status.DONE:
                raise ValueError("Delivery cannot be cancelled if it is done")
            delivery.cancel()

    def _create_delivery_order_and_items(self):
        Delivery = apps.get_model('invensys', 'Delivery')
        delivery = Delivery.objects.create(
            sales_order=self,
            delivery_date=self.delivery_date
        )
        DeliveryItem = apps.get_model('invensys', 'DeliveryItem')
        for item in self.items.all():
            DeliveryItem.objects.create(
                delivery=delivery,
                product=item.product,
                quantity=item.quantity,
                unit=item.unit,
                price=item.price
            )


class BaseOrderItem(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='%(class)s_items')
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class PurchaseOrderItem(BaseOrderItem):
    purchase = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')

    def save(self, *args, **kwargs):
        if self.unit is None:
            pu = ProductUnit.objects.filter(
                product=self.product, is_base_unit=True
            ).select_related("unit").first()
            if pu is not None:
                self.unit = pu.unit
        super().save(*args, **kwargs)
        self.purchase.update_total()

    def delete(self, *args, **kwargs):
        purchase = self.purchase
        super().delete(*args, **kwargs)
        purchase.update_total()

    def __str__(self):
        return f"{self.purchase.number} - {self.product.name}"


class SalesOrderItem(BaseOrderItem):
    sales = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')

    def save(self, *args, **kwargs):
        if self.unit is None:
            pu = ProductUnit.objects.filter(
                product=self.product, is_base_unit=True
            ).select_related("unit").first()
            if pu is not None:
                self.unit = pu.unit
        super().save(*args, **kwargs)
        self.sales.update_total()

    def delete(self, *args, **kwargs):
        sales = self.sales
        super().delete(*args, **kwargs)
        sales.update_total()

    def __str__(self):
        return f"{self.sales.number} - {self.product.name}"
