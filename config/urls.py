from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/auth/', include('djoser.urls')),
    path('api/v1/auth/', include('core_apps.user_auth.urls')),
]

admin.site.site_header = 'NextGen Bank Admin'
admin.site.site_title = 'NextGen Bank Admin Portal'
admin.site.index_title = 'Welcome to NextGen Bank Admin Portal'
