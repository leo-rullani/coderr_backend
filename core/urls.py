"""
URL configuration for the core Django project.

Includes routes for admin and all apps with and without /api/ prefix.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('auth_app.api.urls')),
    path('', include('auth_app.api.urls')),

    path('api/', include('users_app.api.urls')),
    path('', include('users_app.api.urls')),

    path('api/', include('offers_app.api.urls')),
    path('', include('offers_app.api.urls')),

    path('api/', include('orders_app.api.urls')),
    path('', include('orders_app.api.urls')),

    path('api/', include('reviews_app.api.urls')),
    path('', include('reviews_app.api.urls')),

    path('api/', include('core.api.urls')),
    path('', include('core.api.urls')),
]