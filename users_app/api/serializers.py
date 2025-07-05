from rest_framework import serializers
from users_app.models import UserProfile
from auth_app.models import CustomUser

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile including related User fields.
    Email is editable, username and role (type) are read-only.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=False)
    type = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
            "email",
            "created_at",
        ]
        read_only_fields = ["user", "username", "email", "type", "created_at"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        for field in [
            "first_name",
            "last_name",
            "location",
            "tel",
            "description",
            "working_hours",
        ]:
            if rep[field] is None:
                rep[field] = ""
        # Ensure file is treated as empty string if it's None
        if rep.get("file") is None:
            rep["file"] = ""
        return rep

    def update(self, instance, validated_data):
        """
        Updates UserProfile and synchronizes email in related User object if needed.
        """
        user_data = validated_data.pop("user", {})
        email = user_data.get("email")
        if email:
            instance.user.email = email
            instance.user.save()
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer for business profile list with username and role readonly.
    """
    username = serializers.CharField(source="user.username", read_only=True)
    type = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
        ]

    def to_representation(self, instance):
        """
        Return empty fields as empty string instead of None.
        Convert null file to empty string.
        """
        rep = super().to_representation(instance)
        for field in [
            "first_name",
            "last_name",
            "location",
            "tel",
            "description",
            "working_hours",
        ]:
            if rep[field] is None:
                rep[field] = ""
        # Convert file null to empty string
        if rep.get("file") is None:
            rep["file"] = ""
        return rep


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profile list with username and role readonly.
    """
    username = serializers.CharField(source="user.username", read_only=True)
    type = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "uploaded_at",
            "type",
        ]

    def to_representation(self, instance):
        """
        Return empty fields as empty string instead of None.
        """
        rep = super().to_representation(instance)
        for field in ["first_name", "last_name"]:
            if rep[field] is None:
                rep[field] = ""
        # Convert file null to empty string
        if rep.get("file") is None:
            rep["file"] = ""
        return rep