from django.contrib.auth import get_user_model, authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.authtoken.models import Token

from .serializers import RegistrationSerializer

User = get_user_model()


# ------------------------------------------------------------------ #
#  lenient JSON parser: empty body ⇒ {} instead of 400               #
# ------------------------------------------------------------------ #
class LenientJSONParser(parsers.JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type, parser_context)
        except Exception:                 # empty or invalid JSON → treat as {}
            return {}


# ------------------------------------------------------------------ #
#  demo helpers                                                      #
# ------------------------------------------------------------------ #
def _demo_payload(role: str) -> dict:
    username = f"demo_{role}"
    defaults = {"email": f"{username}@example.com"}
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


# ------------------------------------------------------------------ #
#  registration                                                      #
# ------------------------------------------------------------------ #
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
    # … parser_classes, auth, permission bleiben unverändert …

    DEMO_USERS = {"demo_business": "business", "demo_customer": "customer"}

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # ❶  Demo‑Login – gar keine Credentials ODER nur leere Strings
        if not username and not password:
            return Response(
                {
                    "business": _demo_payload("business"),
                    "customer": _demo_payload("customer"),
                },
                status=status.HTTP_200_OK,
            )

        # ❷  Demo‑Login – es steht "demo_customer" o. Ä. im Feld,
        #     aber kein Passwort
        if username in self.DEMO_USERS and not password:
            return Response(
                _demo_payload(self.DEMO_USERS[username]),
                status=status.HTTP_200_OK,
            )

        # ❸  Normales Login
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

        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST,
        )