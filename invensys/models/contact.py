from django.db import models
from .base import BaseModel


class BaseContact(BaseModel):
    class BusinessEntity(models.TextChoices):
        PERORANGAN = 'perorangan', 'Perorangan'
        UD = 'ud', 'UD'
        CV = 'cv', 'CV'
        PT = 'pt', 'PT'
        LAINNYA = 'lainnya', 'Lainnya'

    name = models.CharField(max_length=255, db_index=True)
    business_entity = models.CharField(
        max_length=100,
        choices=BusinessEntity.choices,
        default=BusinessEntity.PERORANGAN
    )
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.get_business_entity_display()}. {self.name}"


class Customer(BaseContact):
    pass


class Supplier(BaseContact):
    pass
