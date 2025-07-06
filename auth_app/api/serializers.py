"""
Serializers for authentication-related endpoints.

`RegistrationSerializer` handles the creation of a new ``CustomUser`` **and**
its associated ``UserProfile`` in one atomic step so that duplicate profile
rows cannot be written even under high concurrency.
"""

from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from auth_app.models import CustomUser
from users_app.models import UserProfile


class RegistrationSerializer(serializers.ModelSerializer):
    """Create a new user account and return an auth token in the view."""
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password", "repeated_password", "role")
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        1. Create the user with a hashed password  
        2. Ensure exactly **one** profile exists (`get_or_create`)  
        3. Ensure exactly **one** token exists (`get_or_create`)
        """
        validated_data.pop("repeated_password")

        # 1) user
        user = CustomUser.objects.create_user(**validated_data)

        # 2) profile – safe against duplicates
        UserProfile.objects.get_or_create(user=user)

        # 3) auth token – returned by the view
        Token.objects.get_or_create(user=user)

        return user