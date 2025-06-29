from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegistrationSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

class RegistrationView(APIView):
    """
    API endpoint for user registration.
    Validates input and returns auth token and user info upon success.
    """
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.get(user=user)
            return Response({
                "token": token.key,
                "username": user.username,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    Authenticates a user and returns a token along with user info.
    """
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "username": user.username,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)