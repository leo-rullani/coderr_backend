from django.http import JsonResponse
from rest_framework import status

def error_404(request, exception=None):
    """
    Global 404 handler that always responds with JSON instead of HTML,
    so automated tests receive `Content‑Type: application/json`.
    """
    return JsonResponse({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
