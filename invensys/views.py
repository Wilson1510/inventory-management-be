from rest_framework import viewsets
from .models import Category, Unit, Product, Customer, Supplier, SalesOrder, PurchaseOrder
from .serializers import (
    CategorySerializer, UnitSerializer, ProductListSerializer, ProductDetailSerializer,
    CustomerListSerializer, CustomerDetailSerializer, SupplierListSerializer,
    SupplierDetailSerializer
)
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Max, Sum, DecimalField, Q
from django.db.models.functions import Coalesce


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


class CustomerViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Customer.objects.all()

        if self.action == 'list':
            valid_status = Q(sales_orders__status=SalesOrder.Status.CONFIRMED)
            queryset = queryset.annotate(
                count_sale_orders=Count('sales_orders', filter=valid_status),
                last_sale_order_date=Max('sales_orders__created_at', filter=valid_status),
                total_sale_amount=Coalesce(
                    Sum('sales_orders__total', filter=valid_status), 0, output_field=DecimalField()
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return CustomerListSerializer
        return CustomerDetailSerializer


class SupplierViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Supplier.objects.all()

        if self.action == 'list':
            valid_status = Q(purchase_orders__status=PurchaseOrder.Status.CONFIRMED)
            queryset = queryset.annotate(
                count_purchase_orders=Count('purchase_orders', filter=valid_status),
                last_purchase_order_date=Max('purchase_orders__created_at', filter=valid_status),
                total_purchase_amount=Coalesce(
                    Sum('purchase_orders__total', filter=valid_status),
                    0,
                    output_field=DecimalField()
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return SupplierListSerializer
        return SupplierDetailSerializer
