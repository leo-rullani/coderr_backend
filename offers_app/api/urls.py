from django.urls import path
from offers_app.api.views import OfferListAPIView, OfferDetailAPIView

urlpatterns = [
    # List endpoint for offers with filter/search/order
    path('offers/', OfferListAPIView.as_view(), name='offer-list'),
    # Detail endpoint, returns a single offer as in the API doc
    path('offers/<int:pk>/', OfferDetailAPIView.as_view(), name='offer-detail'),
]