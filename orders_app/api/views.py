from rest_framework import generics, permissions
from django.db import models
from orders_app.models import Order
from orders_app.api.serializers import OrderSerializer

class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all orders where the user is customer or business partner.
    POST: Create a new order.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            models.Q(customer_user=user) | models.Q(business_user=user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Option: Automatically set customer_user to the current user on create,
        or allow frontend to send both user fields.
        """
        serializer.save()

class OrderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a single order by id (only if involved).
    PATCH/PUT: Update order (optional: restrict to owner).
    DELETE: Delete order (optional: restrict).
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            models.Q(customer_user=user) | models.Q(business_user=user)
        )