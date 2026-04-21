from django.db import models
from .base import BaseModel
from django.utils.text import slugify
from .category import Category
from uuid import uuid4


class Unit(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


def generate_sku_number():
    return uuid4().hex[:10].upper()


class Product(BaseModel):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True)
    sku_number = models.CharField(
        max_length=150, unique=True, default=generate_sku_number, db_index=True
    )
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products', db_index=True
    )
    units = models.ManyToManyField(Unit, through='ProductUnit', related_name='products')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductPrice(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='prices', db_index=True
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_quantity = models.IntegerField(default=1)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='product_prices')

    class Meta:
        unique_together = ('product', 'unit', 'minimum_quantity')

    def __str__(self):
        return f"{self.product.name} - {self.price}"


class ProductUnit(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    multiplier = models.IntegerField(default=1)
    is_base_unit = models.BooleanField(default=False)

    class Meta:
        unique_together = ('product', 'unit')

    def save(self, *args, **kwargs):
        if self.is_base_unit:
            ProductUnit.objects.filter(product=self.product).update(is_base_unit=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.unit.name}"
