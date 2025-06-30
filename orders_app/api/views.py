from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import models
from orders_app.models import Order
from orders_app.api.serializers import OrderSerializer, OrderCreateSerializer
from orders_app.api.permissions import IsCustomerUser

class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating orders.

    GET: Returns a list of orders where the current user is either the customer or the business partner.
    POST: Allows only authenticated users with role 'customer' to create a new order from an OfferDetail.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Returns all orders related to the current user as customer or business user.

        Returns:
            QuerySet: A queryset of Order instances.
        """
        user = self.request.user
        return Order.objects.filter(
            models.Q(customer_user=user) | models.Q(business_user=user)
        ).order_by('-created_at')

    def get_serializer_class(self):
        """
        Returns the appropriate serializer class depending on the request method.

        Returns:
            Serializer: The serializer class for the request.
        """
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        """
        Returns the permission classes for the current request.

        Returns:
            list: List of permission classes to apply.
        """
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomerUser()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        Handles creation of a new order using an OfferDetail.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: The HTTP response with the created order data.
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
    PATCH/PUT: Updates the order (ownership check optional).
    DELETE: Deletes the order (ownership check optional).
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Returns all orders related to the current user as customer or business user.

        Returns:
            QuerySet: A queryset of Order instances.
        """
        user = self.request.user
        return Order.objects.filter(
            models.Q(customer_user=user) | models.Q(business_user=user)
        )