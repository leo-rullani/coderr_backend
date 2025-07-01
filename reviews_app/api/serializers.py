from rest_framework import serializers
from reviews_app.models import Review

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reviewer", "created_at", "updated_at"]

    def validate_rating(self, value):
        """
        Ensure the rating is between 1 and 5.
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        """
        Ensure that a user can only review a business_user once.
        On create: Prevent duplicate reviews for the same business by the same user.
        """
        request = self.context.get("request")
        user = request.user if request else None
        business_user = data.get("business_user") or (self.instance.business_user if self.instance else None)
        # Only check on create, not update
        if self.instance is None and user and business_user:
            if Review.objects.filter(business_user=business_user, reviewer=user).exists():
                raise serializers.ValidationError("You have already reviewed this business.")
        return data