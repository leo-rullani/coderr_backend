"""
Serializers for authentication‑related endpoints.

`RegistrationSerializer` creates a new ``CustomUser`` **and** its matching
profile (+token) in one atomic transaction.
"""
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from auth_app.models import CustomUser
from users_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """Create a new user account (role or legacy type accepted)."""

    repeated_password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=CustomUser.Roles.choices, required=False, write_only=True
    )

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "password",
            "repeated_password",
            "role",
        )
        extra_kwargs = {"password": {"write_only": True}}

    # ------------------------------------------------------------------ #
    def _map_type_to_role(self, attrs: dict) -> dict:
        """Map legacy *type* → *role* if necessary."""
        if "role" not in attrs and "type" in attrs:
            attrs["role"] = attrs.pop("type")
        return attrs

    # ------------------------------------------------------------------ #
    def to_internal_value(self, data):
        return super().to_internal_value(self._map_type_to_role(data.copy()))

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        attrs.pop("repeated_password")
        return attrs

    # ------------------------------------------------------------------ #
    @transaction.atomic
    def create(self, validated_data):
        # 1) user
        user = CustomUser.objects.create_user(**validated_data)

        # 2) profile – keep type in sync with role
        UserProfile.objects.update_or_create(
            user=user, defaults={"type": user.role}
        )

        # 3) token
        Token.objects.get_or_create(user=user)
        return user