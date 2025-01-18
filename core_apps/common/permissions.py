from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View

class IsAccountExecutive(permissions.BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        is_authenticated = request.user.is_authenticated
        has_role_attr = hasattr(request.user, 'role')
        if is_authenticated and has_role_attr:
            return request.user.role == 'ACCOUNT_EXECUTIVE'
        return False
    
class IsTeller(permissions.BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        is_authenticated = request.user.is_authenticated
        has_role_attr = hasattr(request.user, 'role')
        if is_authenticated and has_role_attr:
            return request.user.role == 'TELLER'
        return False
    
class IsBranchManager(permissions.BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        is_authenticated = request.user.is_authenticated
        has_role_attr = hasattr(request.user, 'role')
        if is_authenticated and has_role_attr:
            return request.user.role == 'BRANCH_MANAGER'
        return False
