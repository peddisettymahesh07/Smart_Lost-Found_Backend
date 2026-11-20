from rest_framework import permissions


class IsAdministrator(permissions.BasePermission):
    """Allows access only to authenticated users with admin role or superuser status."""

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser)
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allows object modifications only to the creator or an administrator."""

    def has_object_permission(self, request, view, obj):
        if request.user and (request.user.role == 'admin' or request.user.is_superuser or request.user.is_staff):
            return True
        # For objects with user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'claimant'):
            return obj.claimant == request.user
        return False


class IsFinderOrAdmin(permissions.BasePermission):
    """Allows access to finders or administrators."""

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in ['finder', 'admin'] or request.user.is_staff)
        )
