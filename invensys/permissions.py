from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    message = 'Admin access required.'

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, 'role', None) == 'admin'


class IsAdminOrReadOnly(BasePermission):
    """
    Authenticated users may use safe methods only (GET, HEAD, OPTIONS).
    Admin or superuser required for POST, PUT, PATCH, DELETE.
    """

    message = 'Only admins can modify this resource.'

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if user.is_superuser:
            return True
        return getattr(user, 'role', None) == 'admin'
