from rest_framework import serializers
from auth_app.models import CustomUser
from users_app.models import UserProfile      
from rest_framework.authtoken.models import Token

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Handles user registration with password confirmation.
    Returns token and user data upon successful creation.
    """
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password", "repeated_password", "role"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError({"repeated_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("repeated_password")
        user = CustomUser.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        UserProfile.objects.create(user=user)
        return user