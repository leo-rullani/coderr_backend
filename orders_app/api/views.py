from django.db import models
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from orders_app.models import Order
from orders_app.api.serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
)
from orders_app.api.permissions import IsCustomerUser, IsOrderBusinessUser


# --------------------------------------------------------------------------- #
#  pagination helper                                                          #
# --------------------------------------------------------------------------- #
class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination (page_size 10, override via ?page_size=…)."""
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# --------------------------------------------------------------------------- #
#  list + create                                                              #
# --------------------------------------------------------------------------- #
class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    GET – list all orders where the current user is customer **or** business.  
    POST – create a new order (customers only).
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None            # disabled for this project

    # ----- queryset --------------------------------------------------------
    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            models.Q(customer_user=user) | models.Q(business_user=user)
        ).order_by("-created_at")

    # ----- serializer ------------------------------------------------------
    def get_serializer_class(self):
        return OrderCreateSerializer if self.request.method == "POST" else OrderSerializer

    # ----- permission per method ------------------------------------------
    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomerUser()]
        return [permissions.IsAuthenticated()]

    # ----- create ----------------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# --------------------------------------------------------------------------- #
#  retrieve / patch / delete                                                  #
# --------------------------------------------------------------------------- #
class OrderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    – customer **or** business user involved  
    PATCH  – business user only (update *status* field)  
    DELETE – staff / admin only
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [permissions.IsAuthenticated(), IsOrderBusinessUser()]
        if self.request.method == "DELETE":
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        return OrderStatusUpdateSerializer if self.request.method == "PATCH" else OrderSerializer

    def get_queryset(self):
        return Order.objects.all()     # keeps 403 vs. 404 logic intact

    # ----- object‑level permission check ----------------------------------
    def check_object_permissions(self, request, obj):
        if request.method in ("GET", "DELETE"):
            if request.method == "DELETE" and request.user.is_staff:
                return super().check_object_permissions(request, obj)
            if not (obj.customer_user == request.user or obj.business_user == request.user):
                self.permission_denied(request, message="Not allowed to access this order.")
        return super().check_object_permissions(request, obj)

    # ----- PATCH only 'status' --------------------------------------------
    def partial_update(self, request, *args, **kwargs):
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
        return Response(OrderSerializer(instance).data, status=status.HTTP_200_OK)


# --------------------------------------------------------------------------- #
#  helper mixin for both count views                                          #
# --------------------------------------------------------------------------- #
class _BusinessOrderCountMixin:
    """Shared helpers for order‑count endpoints."""

    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _resolve_user_id(request, path_id):
        """Return business‑user ID from path OR query parameter."""
        return path_id or request.query_params.get("business_user_id")

    @staticmethod
    def _get_business_user(user_id):
        User = get_user_model()
        return User.objects.filter(id=user_id, role="business").first()


# --------------------------------------------------------------------------- #
#  in‑progress count                                                          #
# --------------------------------------------------------------------------- #
class OrderCountAPIView(_BusinessOrderCountMixin, APIView):
    """Return the number of **in_progress** orders for a business user."""

    def get(self, request, business_user_id=None):
        user_id = self._resolve_user_id(request, business_user_id)
        if not user_id:
            return Response(
                {"detail": "business_user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        biz = self._get_business_user(user_id)
        if not biz:
            return Response(
                {"detail": "Business user not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count = Order.objects.filter(business_user=biz, status="in_progress").count()
        return Response({"order_count": count}, status=status.HTTP_200_OK)


# --------------------------------------------------------------------------- #
#  completed count                                                            #
# --------------------------------------------------------------------------- #
class CompletedOrderCountAPIView(_BusinessOrderCountMixin, APIView):
    """Return the number of **completed** orders for a business user."""

    def get(self, request, business_user_id=None):
        user_id = self._resolve_user_id(request, business_user_id)
        if not user_id:
            return Response(
                {"detail": "business_user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        biz = self._get_business_user(user_id)
        if not biz:
            return Response(
                {"detail": "Business user not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count = Order.objects.filter(business_user=biz, status="completed").count()
        return Response({"completed_order_count": count}, status=status.HTTP_200_OK)