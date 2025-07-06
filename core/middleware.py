from django.http import JsonResponse
from rest_framework import status


class ForceJson404Middleware:
    """
    Wandelt *sämtliche* Fehlerseiten (404 oder 403 als HTML/Plain‑Text)
    in JSON um, damit `Content‑Type: application/json` garantiert ist –
    unabhängig von DEBUG=True.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # nur eingreifen, wenn Response NICHT schon JSON ist
        if response.get('Content-Type', '').startswith('application/json'):
            return response

        if response.status_code == 404:
            return JsonResponse({"detail": "Not found."},
                                status=status.HTTP_404_NOT_FOUND)

        if response.status_code == 403:
            # Authentifiziert, aber keine Berechtigung (z. B. IsOwner)
            return JsonResponse({"detail": "Forbidden."},
                                status=status.HTTP_403_FORBIDDEN)

        return response