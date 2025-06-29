from django.urls import path
from offers_app.api.views import OfferListCreateAPIView, OfferDetailAPIView

urlpatterns = [
    path('offers/', OfferListCreateAPIView.as_view(), name='offer-list-create'),
    path('offers/<int:pk>/', OfferDetailAPIView.as_view(), name='offer-detail'),
]