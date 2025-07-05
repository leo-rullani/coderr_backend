from rest_framework.views import APIView
from rest_framework.response import Response
from reviews_app.models import Review
from auth_app.models import CustomUser
from offers_app.models import Offer
from django.db.models import Avg

class BaseInfoView(APIView):
    permission_classes = []

    def get(self, request):
        review_count = Review.objects.count()
        avg_val = Review.objects.aggregate(avg=Avg("rating"))["avg"]
        average_rating = round(float(avg_val), 1) if avg_val is not None else 0.0
        business_profile_count = CustomUser.objects.filter(role='business').count()
        offer_count = Offer.objects.count()

        return Response({
            "review_count": review_count,
            "average_rating": average_rating,
            "business_profile_count": business_profile_count,
            "offer_count": offer_count
        })