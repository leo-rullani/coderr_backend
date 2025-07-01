from rest_framework.views import APIView
from rest_framework.response import Response
from reviews_app.models import Review
from users_app.models import UserProfile
from offers_app.models import Offer  # Passe Import ggf. an!
from django.db.models import Avg

class BaseInfoView(APIView):
    """
    API endpoint that returns platform-wide statistics.

    - review_count: Total number of reviews on the platform.
    - average_rating: Average rating of all reviews (rounded to 1 decimal place).
    - business_profile_count: Number of business user profiles.
    - offer_count: Total number of offers.

    No authentication required.
    """

    permission_classes = []

    def get(self, request):
        """
        Handle GET request for platform statistics.

        Returns:
            Response: JSON object with statistics fields:
                - review_count (int)
                - average_rating (float, 1 decimal)
                - business_profile_count (int)
                - offer_count (int)
        """
        review_count = Review.objects.count()
        avg_val = Review.objects.aggregate(avg=Avg("rating"))["avg"]
        average_rating = round(float(avg_val), 1) if avg_val is not None else 0.0
        business_profile_count = UserProfile.objects.filter(is_customer=False).count()
        offer_count = Offer.objects.count()

        return Response({
            "review_count": review_count,
            "average_rating": average_rating,
            "business_profile_count": business_profile_count,
            "offer_count": offer_count
        })