from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, UnitViewSet, ProductViewSet, CustomerViewSet, SupplierViewSet,
    SalesOrderViewSet, PurchaseOrderViewSet, DeliveryViewSet, ReceiptViewSet,
    DashboardViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'sales-orders', SalesOrderViewSet, basename='salesorder')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'receipts', ReceiptViewSet, basename='receipt')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
