"""
URL routes for Orders API.
Both variants (with and without trailing slash) are accepted so that
frontend tests that omit the slash do not receive HTTP 404.
"""

from django.urls import path, re_path

from orders_app.api.views import (
    OrderListCreateAPIView,
    OrderDetailAPIView,
    OrderCountAPIView,
    CompletedOrderCountAPIView,
)

urlpatterns = [
    # collection + detail
    path("orders/", OrderListCreateAPIView.as_view(), name="order-list-create"),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),

    # -------  counts  -------
    # optional trailing slash – regex `/?$`
    re_path(
        r"^order-count/(?P<business_user_id>\d+)/?$",
        OrderCountAPIView.as_view(),
        name="order-count",
    ),
    re_path(
        r"^completed-order-count/(?P<business_user_id>\d+)/?$",
        CompletedOrderCountAPIView.as_view(),
        name="completed-order-count",
    ),
]