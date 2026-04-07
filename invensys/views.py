from rest_framework import viewsets
from .models import Category, Unit
from .serializers import CategorySerializer, UnitSerializer
from rest_framework.permissions import IsAuthenticated


class UserTrackingMixin:
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class CategoryViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class UnitViewSet(UserTrackingMixin, viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]
