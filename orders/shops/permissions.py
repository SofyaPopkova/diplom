from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    message = "Для изменений необходимы права администратора"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user == request.user.is_superuser
