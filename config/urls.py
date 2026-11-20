"""
URL configuration for Smart Lost & Found Platform.
"""

from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from locations.views import NearbyItemsView


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root_view(request):
    """Interactive API Root listing key platform endpoints."""
    return Response({
        'title': 'Smart Lost & Found Platform REST API',
        'version': '1.0.0',
        'description': 'AI-Based Image Matching & Location-Based Search API',
        'endpoints': {
            'auth': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'profile': '/api/auth/profile/',
                'token_refresh': '/api/auth/token/refresh/',
            },
            'lost_items': '/api/lost-items/',
            'found_items': '/api/found-items/',
            'matches': {
                'list': '/api/matches/',
                'generate': '/api/matches/generate/',
            },
            'locations': {
                'all': '/api/locations/',
                'nearby': '/api/items/nearby/',
            },
            'notifications': {
                'list': '/api/notifications/',
                'read_all': '/api/notifications/read-all/',
            },
            'claims': '/api/claims/',
            'dashboard': {
                'admin_stats': '/api/dashboard/stats/',
                'user_stats': '/api/dashboard/user-stats/',
            }
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root_view, name='api_root'),
    path('api/auth/', include('accounts.urls')),
    path('api/lost-items/', include('lost_items.urls')),
    path('api/found-items/', include('found_items.urls')),
    path('api/matches/', include('matching.urls')),
    path('api/locations/', include('locations.urls')),
    path('api/items/nearby/', NearbyItemsView.as_view(), name='items_nearby_direct'),
    path('api/notifications/', include('notifications.urls')),
    path('api/claims/', include('claims.urls')),
    path('api/dashboard/', include('dashboard.urls')),

    # React Single Page Application (Served seamlessly from Django backend)
    path('', TemplateView.as_view(template_name='index.html'), name='spa_home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Fallback pattern for client-side React routes (excluding api, admin, media, static)
urlpatterns += [
    re_path(r'^(?!api|admin|media|static).*$', TemplateView.as_view(template_name='index.html'), name='spa_fallback'),
]
