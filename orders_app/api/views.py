from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from orders_app.models import Order
from orders_app.api.serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
)
from orders_app.api.permissions import IsCustomerUser, IsOrderBusinessUser
from django.contrib.auth import get_user_model
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class with page size 10, can be overridden by query param 'page_size'.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating orders.

    GET: Returns a paginated list of orders where the current user is either
         the customer or the business partner.
    POST: Allows only authenticated users with role 'customer' to create a new
          order from an OfferDetail.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Pagination enabled here

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
        POST requires authenticated customer, GET requires authentication only.
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
    PATCH: Only the business user (role 'business') can update status (and ONLY status).
    DELETE: Deletes the order (only for admin/staff).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Define permission classes depending on HTTP method:
        - PATCH: business user only
        - DELETE: admin/staff only
        - GET: authenticated users involved in order
        """
        if self.request.method == "PATCH":
            return [permissions.IsAuthenticated(), IsOrderBusinessUser()]
        elif self.request.method == "DELETE":
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """
        Use OrderStatusUpdateSerializer for PATCH, OrderSerializer otherwise.
        """
        if self.request.method == "PATCH":
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        """
        Returns all orders so that unauthorized users receive 403 (forbidden)
        instead of 404 (not found).
        """
        return Order.objects.all()

    def check_object_permissions(self, request, obj):
        """
        Enforces:
        - GET/DELETE: Only customer or business_user involved in the order can access.
        - PATCH: Permission checked by IsOrderBusinessUser.
        - DELETE: Admin/staff allowed.
        """
        if request.method in ("GET", "DELETE"):
            if request.method == "DELETE" and request.user.is_staff:
                return super().check_object_permissions(request, obj)
            if not (obj.customer_user == request.user or obj.business_user == request.user):
                self.permission_denied(request, message="Not allowed to access this order.")
        return super().check_object_permissions(request, obj)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH: Only 'status' field can be updated by business user.
        If other fields included, returns 400 Bad Request.
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

class OrderCountAPIView(APIView):
    """
    Returns the count of 'in_progress' orders for a specific business user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, business_user_id):
        User = get_user_model()
        try:
            business_user = User.objects.get(id=business_user_id, role="business")
        except User.DoesNotExist:
            return Response({"detail": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)
        count = Order.objects.filter(business_user=business_user, status="in_progress").count()
        return Response({"order_count": count}, status=status.HTTP_200_OK)

class CompletedOrderCountAPIView(APIView):
    """
    Returns the count of 'completed' orders for a specific business user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, business_user_id):
        User = get_user_model()
        try:
            business_user = User.objects.get(id=business_user_id, role="business")
        except User.DoesNotExist:
            return Response({"detail": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)
        count = Order.objects.filter(business_user=business_user, status="completed").count()
        return Response({"completed_order_count": count}, status=status.HTTP_200_OK)