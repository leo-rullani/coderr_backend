from rest_framework import serializers
from users_app.models import UserProfile
from auth_app.models import CustomUser

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer für das UserProfile mit Einbindung von Feldern aus dem zugehörigen User (CustomUser).
    E-Mail ist editierbar, Username und Role (type) sind readonly.
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
        """
        Sorgt dafür, dass in der API leere Felder als leerer String statt None zurückgegeben werden.
        """
        rep = super().to_representation(instance)
        for field in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
            if rep[field] is None:
                rep[field] = ""
        return rep

    def update(self, instance, validated_data):
        """
        Aktualisiert das UserProfile und synchronisiert bei Bedarf die Email im verknüpften User-Objekt.
        """
        user_data = validated_data.pop("user", {})
        email = user_data.get("email")
        if email:
            instance.user.email = email
            instance.user.save()
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer für die Business Profile Liste, mit Usernamen und Rolle readonly.
    """
    username = serializers.CharField(source='user.username', read_only=True)
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
            "type"
        ]

    def to_representation(self, instance):
        """
        Leere Felder als leerer String ausgeben statt None.
        """
        rep = super().to_representation(instance)
        for field in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
            if rep[field] is None:
                rep[field] = ""
        return rep


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer für die Customer Profile Liste, mit Usernamen und Rolle readonly.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    type = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "uploaded_at",
            "type"
        ]

    def to_representation(self, instance):
        """
        Leere Felder als leerer String ausgeben statt None.
        """
        rep = super().to_representation(instance)
        for field in ["first_name", "last_name"]:
            if rep[field] is None:
                rep[field] = ""
        return rep