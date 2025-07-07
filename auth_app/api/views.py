"""
Authentication API views.

Endpoints
---------
POST /api/registration/   – create a new account, return auth token
POST /api/login/          – unified login (regular + demo + guest)
"""
from django.contrib.auth import get_user_model, authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from rest_framework.authtoken.models import Token

from users_app.models import UserProfile
from .serializers import RegistrationSerializer

User = get_user_model()


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------
class LenientJSONParser(parsers.JSONParser):
    """Return `{}` instead of 400 for completely empty or malformed JSON."""
    def parse(self, *args, **kwargs):
        try:
            return super().parse(*args, **kwargs)
        except Exception:
            return {}  # silently swallow parse errors


def _ensure_profile(user: User, role: str) -> None:
    """
    Guarantee that exactly one `UserProfile` exists and its `type`
    matches the user’s role (`customer` / `business`).
    """
    UserProfile.objects.update_or_create(
        user=user,
        defaults={"type": role},
    )


def _demo_payload(role: str) -> dict:
    """
    Return a ready‑to‑use demo token payload for the given `role`.
    A demo user + profile are created on first use.
    """
    username = f"demo_{role}"
    defaults = {"email": f"{username}@example.com"}
    if hasattr(User, "role"):
        defaults["role"] = role

    user, created = User.objects.get_or_create(username=username, defaults=defaults)
    if created:
        user.set_password("demo123")
        user.save()
    _ensure_profile(user, role)

    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "username": user.username,
        "email": user.email,
        "user_id": user.id,
        "role": role,
    }


# -------------------------------------------------------------------------
# Views
# -------------------------------------------------------------------------
class RegistrationView(APIView):
    """Create a new user and immediately return an auth token."""
    parser_classes = [LenientJSONParser, parsers.FormParser]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        _ensure_profile(user, getattr(user, "role", "customer"))

        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "username": user.username,
                "email": user.email,
                "user_id": user.id,
                "role": user.role,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Unified login endpoint with demo and guest shortcuts.

    Match order (first rule that applies wins):

    1. **Empty body**               → both demo tokens (`business`, `customer`)
    2. **Only `role`/`type` field** → single demo token for that role
    3. **Username `demo_*`**        → demo token (no password)
    4. **Guest creds `kevin/andrey`**
       – default password is used when omitted
       – user & profile are created/updated as needed
    5. **Regular username+password**
    """
    parser_classes = [LenientJSONParser, parsers.FormParser]
    authentication_classes = []
    permission_classes = []

    # (front‑end) guest users
    GUEST_MAP = {
        "kevin":  ("business", "asdasd24"),
        "andrey": ("customer", "asdasd"),
    }
    DEMO_USERNAMES = {"demo_business": "business", "demo_customer": "customer"}
    DEMO_ROLES = {"business", "customer"}

    # ---------------------------------------------------------------------
    def _token_response(self, user: User) -> Response:
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "username": user.username,
                "email": user.email,
                "user_id": user.id,
                "role": getattr(user, "role", "customer"),
            },
            status=status.HTTP_200_OK,
        )

    def _ensure_guest_user(self, username: str, password: str, role: str) -> User:
        defaults = {"email": f"{username}@example.com"}
        if hasattr(User, "role"):
            defaults["role"] = role

        user, created = User.objects.get_or_create(username=username, defaults=defaults)
        if created or not user.check_password(password):
            user.set_password(password)
            user.save()
        _ensure_profile(user, role)
        return user

    # ---------------------------------------------------------------------
    def post(self, request):
        data = request.data
        username = data.get("username", "").strip()
        password = data.get("password", "")
        # accept both aliases
        role = (data.get("role") or data.get("type") or "").strip().lower()

        # 1) completely empty body  ---------------------------------------
        if not username and not password and not role:
            return Response(
                {
                    "business": _demo_payload("business"),
                    "customer": _demo_payload("customer"),
                },
                status=status.HTTP_200_OK,
            )

        # 2) only role/type  ----------------------------------------------
        if role in self.DEMO_ROLES and not username and not password:
            return Response(_demo_payload(role), status=status.HTTP_200_OK)

        # 3) demo username without pwd  -----------------------------------
        if username in self.DEMO_USERNAMES and not password:
            return Response(
                _demo_payload(self.DEMO_USERNAMES[username]),
                status=status.HTTP_200_OK,
            )

        # 4) guest credentials  -------------------------------------------
        if username in self.GUEST_MAP:
            expected_role, default_pw = self.GUEST_MAP[username]
            pwd = password or default_pw
            user = authenticate(username=username, password=pwd)
            if not user:
                user = self._ensure_guest_user(username, pwd, expected_role)
            return self._token_response(user)

        # 5) regular login  -----------------------------------------------
        user = authenticate(username=username, password=password)
        if user:
            _ensure_profile(user, getattr(user, "role", "customer"))
            return self._token_response(user)

        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )