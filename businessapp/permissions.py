from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated as DRFIsAuthenticated


class IsAuthenticated(DRFIsAuthenticated):
    message = 'Demo accounts are read-only.'

    def has_permission(self, request, view):
        is_auth = super().has_permission(request, view)
        if not is_auth:
            return False
        if getattr(request.user, 'role', None) == 'demo' and request.method not in SAFE_METHODS:
            return False
        return True


class IsAdmin(BasePermission):
    message = 'Admin access required.'

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        if getattr(user, 'role', None) == 'demo' and request.method in SAFE_METHODS:
            return True
            
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
