from django.urls import path
from . import views_mobile

urlpatterns = [
    path('authuser', views_mobile.authuser, name='index'),
    path('groupstatus', views_mobile.groupstatus, name='index'),
    path('sendphotogroup', views_mobile.sendphotogroup, name='index'),
    path('setstatus', views_mobile.setstatus, name='index'),
    path('register', views_mobile.register, name='index'),
    path('childstatus', views_mobile.childstatus, name='index'),
    path('childphoto', views_mobile.childphoto, name='index'),
    path('childhistory', views_mobile.childhistory, name='index')   
]
