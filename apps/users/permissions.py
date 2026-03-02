from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import UserRole


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and 
                    (request.user.role == UserRole.ADMIN or request.user.is_superuser))
    
class IsRoleAllowed(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        allowed_roles = getattr(view, 'allowed_roles', None)

        if allowed_roles is None:
            return False  

        return request.user.role in allowed_roles
    
class IsRoleOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in view.allowed_roles
        )