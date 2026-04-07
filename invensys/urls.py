from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, UnitViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'units', UnitViewSet, basename='unit')

urlpatterns = [
    path('', include(router.urls)),
]
