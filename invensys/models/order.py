from django.db import models
from .base import BaseModel
from .contact import Customer, Supplier
from .product import Product
from django.db.models import Sum, F


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
            self.number = self.generate_number()
            super().save(update_fields=["number"])

    def calculate_total(self):
        return self.items.aggregate(total=Sum(F("price") * F("quantity")))["total"] or 0

    def update_total(self):
        self.total = self.calculate_total()
        self.save(update_fields=["total"])

    def __str__(self):
        return self.number


class PurchaseOrder(BaseOrder):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='purchase_orders'
    )
    arrival_date = models.DateField(null=True, blank=True)

    def generate_number(self):
        return f"P{self.id:05d}"


class SalesOrder(BaseOrder):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='sales_orders'
    )
    delivery_date = models.DateField(null=True, blank=True)

    def generate_number(self):
        return f"S{self.id:05d}"


class BaseOrderItem(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='%(class)s_items')
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.update_total()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.update_total()

    def __str__(self):
        return f"{self.order.number} - {self.product.name}"


class PurchaseOrderItem(BaseOrderItem):
    purchase = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')


class SalesOrderItem(BaseOrderItem):
    sales = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
