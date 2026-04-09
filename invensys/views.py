from rest_framework import viewsets, status, mixins
from .models import (
    Category, Unit, Product, Customer, Supplier, SalesOrder, PurchaseOrder,
    Delivery, Receipt,
)
from .serializers import (
    CategorySerializer, UnitSerializer, ProductListSerializer, ProductDetailSerializer,
    CustomerListSerializer, CustomerDetailSerializer, SupplierListSerializer,
    SupplierDetailSerializer, SalesOrderListSerializer, SalesOrderDetailSerializer,
    PurchaseOrderListSerializer, PurchaseOrderDetailSerializer,
    DeliveryListSerializer, DeliveryDetailSerializer,
    ReceiptListSerializer, ReceiptDetailSerializer,
)
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Max, Sum, DecimalField, Q
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.response import Response


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


class SalesOrderViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    queryset = SalesOrder.objects.select_related('customer').prefetch_related(
        'items__product', 'items__unit'
    )

    def get_serializer_class(self):
        if self.action == 'list':
            return SalesOrderListSerializer
        return SalesOrderDetailSerializer

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        try:
            order.confirm()
            return Response(
                {"detail": "Sales Order berhasil dikonfirmasi."},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order.cancel()
            return Response(
                {"detail": "Sales Order berhasil dibatalkan."},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('supplier').prefetch_related(
        'items__product', 'items__unit'
    )

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        return PurchaseOrderDetailSerializer

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        try:
            order.confirm()
            return Response(
                {"detail": "Purchase Order berhasil dikonfirmasi."},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order.cancel()
            return Response(
                {"detail": "Purchase Order berhasil dibatalkan."},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeliveryViewSet(UserTrackingMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Delivery.objects.select_related(
        'sales_order', 'sales_order__customer'
    ).prefetch_related('items__product', 'items__unit')

    def get_serializer_class(self):
        if self.action == 'list':
            return DeliveryListSerializer
        return DeliveryDetailSerializer

    @action(detail=True, methods=['post'])
    def done(self, request, pk=None):
        delivery = self.get_object()
        try:
            delivery.done(request.user)
            return Response(
                {"detail": "Delivery berhasil diselesaikan."}, status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        delivery = self.get_object()
        try:
            delivery.cancel()
            return Response(
                {"detail": "Delivery berhasil dibatalkan."}, status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReceiptViewSet(UserTrackingMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Receipt.objects.select_related(
        'purchase_order', 'purchase_order__supplier'
    ).prefetch_related('items__product', 'items__unit')

    def get_serializer_class(self):
        if self.action == 'list':
            return ReceiptListSerializer
        return ReceiptDetailSerializer

    @action(detail=True, methods=['post'])
    def done(self, request, pk=None):
        receipt = self.get_object()
        try:
            receipt.done(request.user)
            return Response(
                {"detail": "Receipt berhasil diselesaikan."}, status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        receipt = self.get_object()
        try:
            receipt.cancel()
            return Response(
                {"detail": "Receipt berhasil dibatalkan."}, status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
