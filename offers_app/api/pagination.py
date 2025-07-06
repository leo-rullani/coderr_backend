"""
Project‑wide pagination rules.

Allows clients to override the default page size via the ``page_size`` query
parameter while keeping a reasonable upper bound.
"""

from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Standard paginator with a client‑controlled page_size parameter."""
    page_size_query_param = "page_size"       # enables ?page_size=X
    max_page_size = 50                        # hard upper limit
