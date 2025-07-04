from rest_framework.permissions import BasePermission
import logging

logger = logging.getLogger(__name__)

class IsCustomerUser(BasePermission):
    """
    Allows access only to users with role 'customer'.
    Used to restrict order creation to customers only.
    """
    message = "Only customers can create orders."

    def has_permission(self, request, view):
        """
        Checks if the user is authenticated and has the 'customer' role.

        Args:
            request: HTTP request.
            view: View being accessed.

        Returns:
            bool: True if user is authenticated and role is 'customer', else False.
        """
        return request.user.is_authenticated and getattr(request.user, "role", None) == "customer"

class IsOrderBusinessUser(BasePermission):
    """
    Allows access only to the business_user of the order with role 'business'.
    Used to restrict updating order status to the related business user only.
    """
    message = "Only the business user of this order can update the status."

    def has_object_permission(self, request, view, obj):
        """
        Checks if the user is authenticated, has role 'business' and
        is the business_user of the order instance.

        Args:
            request: HTTP request.
            view: View being accessed.
            obj: Order object.

        Returns:
            bool: True if user matches the order's business_user and role is 'business'.
        """
        is_authenticated = request.user.is_authenticated
        is_business = getattr(request.user, "role", None) == "business"
        is_owner = (obj.business_user.id == request.user.id)

        # Optional: Aktivieren, um Debug-Ausgaben zu sehen
        # logger.debug(f"User authenticated: {is_authenticated}")
        # logger.debug(f"User role is business: {is_business}")
        # logger.debug(f"User is business_user of order: {is_owner}")
        # logger.debug(f"Request user ID: {request.user.id}, Order business_user ID: {obj.business_user.id}")

        return is_authenticated and is_business and is_owner