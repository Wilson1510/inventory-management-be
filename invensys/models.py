from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
    )

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Unit(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    sku_number = models.CharField(max_length=150, unique=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    units = models.ManyToManyField(Unit, through='ProductUnit', related_name='products')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductPrice(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
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
