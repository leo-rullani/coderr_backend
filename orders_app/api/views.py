from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import models
from orders_app.models import Order
from orders_app.api.serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
)
from orders_app.api.permissions import IsCustomerUser, IsOrderBusinessUser

class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating orders.

    GET: Returns a paginated list of orders where the current user is either the customer or the business partner.
    POST: Allows only authenticated users with role 'customer' to create a new order from an OfferDetail.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Returns all orders related to the current user as customer or business user.
        """
        user = self.request.user
        return Order.objects.filter(
            models.Q(customer_user=user) | models.Q(business_user=user)
        ).order_by('-created_at')

    def get_serializer_class(self):
        """
        Returns the appropriate serializer class depending on the request method.
        """
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        """
        Returns the permission classes for the current request.
        """
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomerUser()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        Handles creation of a new order using an OfferDetail.
        """
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        output_serializer = OrderSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class OrderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a single order.

    GET: Retrieves an order by id if the user is involved.
    PATCH: Only the business user (role 'business') can update status (and ONLY status!).
    DELETE: Deletes the order (only for admin/staff!).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        PATCH: Only business_user ('business') can update status.
        DELETE: Only staff/admin can delete.
        Other: Any involved user (customer or business).
        """
        if self.request.method == "PATCH":
            return [permissions.IsAuthenticated(), IsOrderBusinessUser()]
        elif self.request.method == "DELETE":
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """
        PATCH: Use OrderStatusUpdateSerializer (only status allowed).
        Other: Use OrderSerializer.
        """
        if self.request.method == "PATCH":
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        """
        Gibt ALLE Orders zurück (damit auch andere Business-User 403 kriegen, nicht 404!)
        """
        return Order.objects.all()

    def check_object_permissions(self, request, obj):
        """
        Für GET/DELETE: Nur customer oder business_user dürfen überhaupt lesen/löschen.
        Für PATCH: Permission wird in IsOrderBusinessUser gemacht (nur business_user darf patchen).
        Für DELETE: Nur Admin (IsAdminUser) und Order-Beteiligte sehen 403, Rest 404.
        """
        if request.method in ("GET", "DELETE"):
            # Für Admins: dürfen immer alles löschen
            if request.method == "DELETE" and request.user.is_staff:
                return super().check_object_permissions(request, obj)
            # Für andere: Zugriff nur, wenn Kunde oder Business-User beteiligt ist
            if not (obj.customer_user == request.user or obj.business_user == request.user):
                self.permission_denied(request, message="Not allowed to access this order.")
        return super().check_object_permissions(request, obj)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH: Updates only the 'status' field if the user is the business user.
        Only 'status' allowed, any other field = 400 error!
        """
        if set(request.data.keys()) != {"status"}:
            return Response(
                {"detail": "Only 'status' field can be updated via PATCH."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.refresh_from_db()
        output_serializer = OrderSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_200_OK)