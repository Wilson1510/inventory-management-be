from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, UserViewSet, CategoryViewSet, UnitViewSet, ProductViewSet, CustomerViewSet,
    SupplierViewSet, SalesOrderViewSet, PurchaseOrderViewSet, DeliveryViewSet, ReceiptViewSet,
    DashboardViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
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
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('', include(router.urls)),
]
