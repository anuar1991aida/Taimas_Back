from django.urls import path
from . import views_integrations

urlpatterns = [
    path('dirs', views_integrations.dirs, name='index'),
    path('allvisits', views_integrations.allvisits, name='index'),
    path('actionorgs', views_integrations.actionorgs, name='index'),
    path('geterrorgroup', views_integrations.geterrorgroup, name='index'),  
    path('insertdesc', views_integrations.insertdesc, name='index')     
]
