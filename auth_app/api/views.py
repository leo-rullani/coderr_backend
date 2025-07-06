from django.contrib.auth import get_user_model, authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .serializers import RegistrationSerializer

User = get_user_model()


def _demo_payload(role: str) -> dict:
    username = f"demo_{role}"
    email = f"{username}@example.com"
    defaults = {"email": email}
    if hasattr(User, "role"):
        defaults["role"] = role
    user, created = User.objects.get_or_create(username=username, defaults=defaults)
    if created:
        user.set_password("demo123")
        user.save()
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "username": user.username,
        "email": user.email,
        "user_id": user.id,
        "role": role,
    }


class RegistrationView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.get(user=user)
            return Response(
                {
                    "token": token.key,
                    "username": user.username,
                    "email": user.email,
                    "user_id": user.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    * Normal login – POST body with username & password  
    * Demo login  – empty POST body  → returns both demo tokens
    """

    authentication_classes = []          # allow anonymous
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # demo login: body missing or empty strings
        if not (username or password):
            return Response(
                {
                    "business": _demo_payload("business"),
                    "customer": _demo_payload("customer"),
                },
                status=status.HTTP_200_OK,
            )

        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "username": user.username,
                    "email": user.email,
                    "user_id": user.id,
                },
                status=status.HTTP_200_OK,
            )
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
