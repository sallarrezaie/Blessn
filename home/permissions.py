from rest_framework import permissions


class IsGetOrIsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == 'GET':
            return True

        return request.user and request.user.is_authenticated


class IsPostOrIsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == 'POST' or request.method == 'GET':
            return True

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        if request.method == 'PATCH' or request.method == 'PUT' or request.method == "DELETE":
            if obj == request.user:
                return True
        
        if request.method == 'GET':
            return True

        return False


class IsAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser and request.user.is_authenticated


class IsGetOrAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user and request.user.is_authenticated

        return request.user and request.user.is_authenticated and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method == 'GET':
            return request.user and request.user.is_authenticated

        return False
