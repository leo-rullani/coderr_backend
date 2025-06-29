from django_filters import rest_framework as filters
from offers_app.models import Offer

class OfferFilter(filters.FilterSet):
    """
    FilterSet for filtering Offer objects by creator,
    min_price, and max_delivery_time.
    """
    min_price = filters.NumberFilter(field_name="min_price", lookup_expr="gte")
    max_delivery_time = filters.NumberFilter(
        field_name="min_delivery_time", lookup_expr="lte"
    )
    creator_id = filters.NumberFilter(field_name="user_id")

    class Meta:
        model = Offer
        fields = ["creator_id", "min_price", "max_delivery_time"]