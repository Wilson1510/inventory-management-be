from rest_framework import viewsets
from .models import Category, Unit, Product
from .serializers import (
    CategorySerializer, UnitSerializer, ProductListSerializer, ProductDetailSerializer
)
from rest_framework.permissions import IsAuthenticated


class UserTrackingMixin:
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class CategoryViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class UnitViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class ProductViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').prefetch_related(
        'prices__unit',
        'productunit_set__unit'
    )

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer
