from django.urls import path
from orders_app.api.views import (
    OrderListCreateAPIView,
    OrderDetailAPIView,
    OrderCountAPIView,
    CompletedOrderCountAPIView,   
)

urlpatterns = [
    path('orders/', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('order-count/<int:business_user_id>/', OrderCountAPIView.as_view(), name='order-count'),
    path('completed-order-count/<int:business_user_id>/', CompletedOrderCountAPIView.as_view(), name='completed-order-count'),  # <--- NEU
]