"""
Global pagination class for the entire REST API.

It behaves like DRF's default ``PageNumberPagination`` but lets the client
override the page size with the ``page_size`` query parameter, capped at 100.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Default paginator: page number + optional page‑size override."""
    page_size = 10                    # server‑side default
    page_size_query_param = "page_size"
    max_page_size = 100               # safety cap