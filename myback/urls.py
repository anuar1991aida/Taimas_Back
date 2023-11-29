from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('api/', include('serviceback.urls_mobile')),
    path('srv/', include('serviceback.urls_admin')),
    path('srvint/', include('serviceback.urls_integrations')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
