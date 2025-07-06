from rest_framework import serializers
from reviews_app.models import Review
from django.contrib.auth import get_user_model

User = get_user_model()
class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the *Review* model.

    * `business_user`  – primary‑key of a user whose role is **business**
    * `reviewer`       – set automatically from the request user
    * `rating`         – integer between 1 and 5
    """

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
        """Ensure *rating* is within the accepted 1‑5 range."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_business_user(self, value: User):
        """
        Ensure the referenced user actually *is* a business account.
        """
        if getattr(value, "role", None) != "business":
            raise serializers.ValidationError("business_user must have role 'business'.")
        return value

    def validate(self, data):
        """
        Prevent duplicate reviews: a customer may review any given business
        account **only once**.
        """
        request = self.context.get("request")
        user = request.user if request else None
        business_user = data.get("business_user") or (
            self.instance.business_user if self.instance else None
        )

        if self.instance is None and user and business_user:
            if Review.objects.filter(business_user=business_user, reviewer=user).exists():
                raise serializers.ValidationError(
                    "You have already reviewed this business."
                )
        return data
