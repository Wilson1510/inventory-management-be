from django.db import models
from django.db.models import Sum, F
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


class BaseContact(BaseModel):
    class BusinessEntity(models.TextChoices):
        PERORANGAN = 'perorangan', 'Perorangan'
        UD = 'ud', 'UD'
        CV = 'cv', 'CV'
        PT = 'pt', 'PT'
        LAINNYA = 'lainnya', 'Lainnya'

    name = models.CharField(max_length=255)
    business_entity = models.CharField(
        max_length=100,
        choices=BusinessEntity.choices,
        default=BusinessEntity.PERORANGAN
    )
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_business_entity_display()}. {self.name}"


class Customer(BaseContact):
    pass


class Supplier(BaseContact):
    pass


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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
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
