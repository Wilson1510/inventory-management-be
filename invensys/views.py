from rest_framework import viewsets, status, mixins
from django.contrib.auth import get_user_model
from .models import (
    Category, Unit, Product, Customer, Supplier, SalesOrder, PurchaseOrder,
    Delivery, Receipt,
)
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserSerializer, UserMeSerializer, UserPasswordResetSerializer, UserChangePasswordSerializer,
    CategorySerializer, UnitSerializer, ProductListSerializer, ProductDetailSerializer,
    CustomerListSerializer, CustomerDetailSerializer, SupplierListSerializer,
    SupplierDetailSerializer, SalesOrderListSerializer, SalesOrderDetailSerializer,
    PurchaseOrderListSerializer, PurchaseOrderDetailSerializer,
    DeliveryListSerializer, DeliveryDetailSerializer,
    ReceiptListSerializer, ReceiptDetailSerializer,
    DashboardMetricsSerializer, DashboardTopDataSerializer,
)
from .services.dashboard import metrics_payload, top_data_payload
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin, IsAdminOrReadOnly
from django.db.models import Count, Max, Sum, DecimalField, Q
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer


class UserTrackingMixin:
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class ProtectedDeleteMixin:
    """Maps django.db ProtectedError on delete() to 409 JSON for API clients."""

    protected_delete_detail = (
        'This record cannot be deleted because other records depend on it.'
    )
    protected_delete_code = 'protected_delete'

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {
                    'detail': self.protected_delete_detail,
                    'code': self.protected_delete_code,
                },
                status=status.HTTP_409_CONFLICT,
            )


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_permissions(self):
        if getattr(self, 'action', None) in ('me', 'change_password'):
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            return Response(UserMeSerializer(request.user).data)
        serializer = UserMeSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        serializer = UserPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'message': 'Password reset successfully'})

    @action(detail=False, methods=['patch'], url_path='me/change-password')
    def change_password(self, request):
        serializer = UserChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'message': 'Password changed successfully'})


class CategoryViewSet(UserTrackingMixin, ProtectedDeleteMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    protected_delete_detail = (
        'This category cannot be deleted because it has '
        'one or more associated products.'
    )
    protected_delete_code = 'category_has_products'


class UnitViewSet(UserTrackingMixin, ProtectedDeleteMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    protected_delete_detail = (
        'This unit cannot be deleted because it is still referenced by '
        'sales or purchase order items.'
    )
    protected_delete_code = 'unit_has_references'


class ProductViewSet(UserTrackingMixin, ProtectedDeleteMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]

    queryset = Product.objects.select_related('category').prefetch_related(
        'prices__unit',
        'productunit_set__unit'
    )

    protected_delete_detail = (
        'This product cannot be deleted because it is still referenced by '
        'sales or purchase order items.'
    )
    protected_delete_code = 'product_has_references'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer


class CustomerViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['get'], url_path='metrics')
    def metrics(self, request):
        return Response(DashboardMetricsSerializer(instance=metrics_payload()).data)

    @action(detail=False, methods=['get'], url_path='top-data')
    def top_data(self, request):
        return Response(DashboardTopDataSerializer(instance=top_data_payload()).data)
