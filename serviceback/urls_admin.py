from django.urls import path
from . import views_admin

urlpatterns = [
    path('authuser', views_admin.authuser, name='index'),
    path('updateChilds', views_admin.updateChilds, name='index'), 
    path('gettabelbyday', views_admin.gettabelbyday, name='index'),

    path('grouplist', views_admin.grouplist, name='index'),
    path('groupedit', views_admin.groupedit, name='index'),

    path('childlist', views_admin.childlist, name='index'),
    path('childedit', views_admin.childedit, name='index'),
    path('getchildbyinn', views_admin.getchildbyinn, name='index'),

    path('metodistlist', views_admin.metodistlist, name='index'),
    path('metodistedit', views_admin.metodistedit, name='index'),

    path('importfile', views_admin.importfile, name='index'),
    path('startpage', views_admin.startpage, name='index')
]
