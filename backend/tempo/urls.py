import os

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def spa(request, path=''):
    index = settings.BASE_DIR / 'static' / 'frontend' / 'index.html'
    if os.path.exists(index):
        return FileResponse(open(index, 'rb'), content_type='text/html')
    return HttpResponse(
        '<p>Frontend not built. Run: <code>cd frontend && npm run build</code></p>',
        status=503,
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('habits.urls')),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    # Catch-all: let React Router handle all non-API paths
    path('', spa),
    path('<path:path>', spa),
]
