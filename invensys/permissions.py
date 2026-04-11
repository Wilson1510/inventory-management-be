from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = 'Admin access required.'

    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True
        return getattr(user, 'role', None) == 'admin'
