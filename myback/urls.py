from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('serviceback.urls_mobile')),
    path('srv/', include('serviceback.urls_admin')),
    path('admin/', admin.site.urls),
]
