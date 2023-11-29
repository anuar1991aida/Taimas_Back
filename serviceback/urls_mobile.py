from django.urls import path
from . import views_mobile

urlpatterns = [
    path('authuser', views_mobile.authuser, name='index'),
    
    path('sendphotogroup', views_mobile.sendphotogroup, name='index'),
    # path('newsendphoto', views_mobile.newsendphoto, name='index'),
    path('childhistory', views_mobile.childhistory, name='index'),
    path('sendphoto512', views_mobile.sendphoto512, name='index'),
    path('register512', views_mobile.register512, name='index'),
    path('register1024', views_mobile.register1024, name='index'),



    path('sendphotochild', views_mobile.sendphotochild, name='index'),
    path('authuser1024', views_mobile.authuser1024, name='index'),
    path('groupstatus', views_mobile.groupstatus, name='index'),
    path('setstatus', views_mobile.setstatus, name='index'),
    path('childphoto', views_mobile.childphoto, name='index'),
    path('childstatus', views_mobile.childstatus, name='index'),
    path('register', views_mobile.register, name='index'),
    path('register128', views_mobile.register128, name='index'),
    path('sendphoto128', views_mobile.sendphoto128, name='index'),
    path('getFakeImgUrl', views_mobile.getFakeImgUrl, name='index'),
    path('changestatusbyadm', views_mobile.changestatusbyadm, name='index'),
    path('getdescriptors', views_mobile.getdescriptors, name='index'),
    path('testdesc', views_mobile.testdesc, name='index'),
]
