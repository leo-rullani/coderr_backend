from django.urls import path
from .views import (
    BusinessProfileListView,
    CustomerProfileListView,
    BusinessProfileDetailView,
    BusinessProfileRefUpdateView,      
    UserProfileUniversalDetailView,
)

urlpatterns = [
    path(
        "profile/business/<str:ref>/",
        BusinessProfileRefUpdateView.as_view(),
        name="business-profile-ref-update",
    ),

    path(
        "profile/business/",
        BusinessProfileDetailView.as_view(),
        name="business-profile-detail",
    ),

    path(
        "profile/<str:ref>/",
        UserProfileUniversalDetailView.as_view(),
        name="user-profile-universal-detail",
    ),

    path("profiles/business/", BusinessProfileListView.as_view(), name="business-profiles"),
    path("profiles/customer/", CustomerProfileListView.as_view(), name="customer-profiles"),
]