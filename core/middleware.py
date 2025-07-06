# core/middleware.py
from django.http import JsonResponse
from rest_framework import status

class ForceJson404Middleware:
    """Ensure 404 responses are JSON even when DEBUG=True."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404 and response.get('Content-Type', '').startswith('text/html'):
            return JsonResponse({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return response
