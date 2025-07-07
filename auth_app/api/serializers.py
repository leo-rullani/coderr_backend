"""
Serializers for authentication‑related endpoints.

`RegistrationSerializer` creates a new ``CustomUser`` **and** its matching
profile (+token) in one atomic transaction.

Key points
----------
* **Alias support:** Accept both ``role`` *and* legacy ``type`` fields.
* **Role validation:** Ensures the incoming role is one of the configured
  choices (`customer`/`business`).
"""

from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from auth_app.models import CustomUser
from users_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Create a new user account.

    Optional fields
    ---------------
    * ``role`` – preferred field used by the API doc  
    * ``type`` – legacy alias still accepted for backward compatibility
    """
    repeated_password = serializers.CharField(write_only=True)
    # allow ``role`` to be omitted; default is set in the model/manager
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
            "role",            # ← will be populated from "type" if necessary
        )
        extra_kwargs = {"password": {"write_only": True}}

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _map_type_to_role(self, attrs: dict) -> dict:
        """Map legacy *type* -> *role* if a role is missing."""
        if "role" not in attrs and "type" in attrs:
            attrs["role"] = attrs.pop("type")
        return attrs

    # ---------------------------------------------------------------------
    # Validation & creation
    # ---------------------------------------------------------------------
    def to_internal_value(self, data):
        """Called *before* field validation – ideal place for alias mapping."""
        return super().to_internal_value(self._map_type_to_role(data.copy()))

    def validate(self, attrs):
        # Password double‑entry check
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        attrs.pop("repeated_password")
        return attrs

    # ---------------------------------------------------------------------
    @transaction.atomic
    def create(self, validated_data):
        """
        1. Create user (password is hashed by the custom manager)  
        2. Create a generic UserProfile (always succeeds)  
        3. Create auth token – returned by the view
        """
        # 1) user
        user = CustomUser.objects.create_user(**validated_data)

        # 2) profile – safe against duplicates
        UserProfile.objects.get_or_create(user=user)

        # 3) token – identical call in the view, but harmless (get_or_create)
        Token.objects.get_or_create(user=user)

        return user