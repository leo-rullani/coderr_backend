from django.urls import path
from offers_app.api.views import OfferListAPIView

urlpatterns = [
    # List endpoint for offers with filter/search/order
    path('offers/', OfferListAPIView.as_view(), name='offer-list'),
]