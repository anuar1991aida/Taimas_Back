from django.urls import path
from . import views_admin

urlpatterns = [
    path('authuser', views_admin.authuser, name='index'),
    path('getinfo', views_admin.getinfo, name='index'), #нужно удалить
    path('getinfoorg', views_admin.getinfoorg, name='index'),    #нужно удалить
    path('sendmail', views_admin.sendmail, name='index'),    
    path('getoblasttype', views_admin.getoblasttype, name='index'),    
    path('getregiontype', views_admin.getregiontype, name='index'),
    path('changepass', views_admin.changepass, name='index'),    
    path('statusphoto', views_admin.statusphoto, name='index'), #нужно удалить
    path('updateChilds', views_admin.updateChilds, name='index'), #нужно удалить
    path('gettabelbyday', views_admin.gettabelbyday, name='index'), #нужно удалить
    path('gettabelbymonth', views_admin.gettabelbymonth, name='index'),
    path('gettabelbym', views_admin.gettabelbym, name='index'), #нужно удалить
    path('gettabel', views_admin.gettabel, name='index'), #нужно удалить
    path('editvisit', views_admin.editvisit, name='index'),
    path('deletevisit', views_admin.deletevisit, name='index'),
    
    path('grouplist', views_admin.grouplist, name='index'),
    path('groupedit', views_admin.groupedit, name='index'),
    path('childlist', views_admin.childlist, name='index'),
    path('childselect', views_admin.childselect, name='index'),
    path('childedit', views_admin.childedit, name='index'),
    path('childstatus', views_admin.childstatus, name='index'),
    path('childstatusbyiin', views_admin.childstatusbyiin, name='index'),    
    path('childphoto', views_admin.childphoto, name='index'), #нужно удалить
    path('allstatus', views_admin.allstatus, name='index'),
    path('getchildbyinn', views_admin.getchildbyinn, name='index'),
    path('metodistlist', views_admin.metodistlist, name='index'),
    path('metodistedit', views_admin.metodistedit, name='index'),
    path('importfile', views_admin.importfile, name='index'),
    path('startpage', views_admin.startpage, name='index'),   

    path('startpageadmin', views_admin.startpageadmin, name='index'),
    path('getorglist', views_admin.getorglist, name='index'),
    path('getorgelement', views_admin.getorgelement, name='index'),
    path('orgedit', views_admin.orgedit, name='index'),
    path('grouplistadmin', views_admin.grouplistadmin, name='index'),
    path('childlistadmin', views_admin.childlistadmin, name='index'),
    path('metodistlistadmin', views_admin.metodistlistadmin, name='index'),
    path('requestlist', views_admin.requestlist, name='index'),
    path('suborg', views_admin.suborg, name='index'),
    path('getnonsuborg', views_admin.nonsuborg, name='index'),
    path('addsuborg', views_admin.addsuborg, name='index'),
    path('delete_suborg', views_admin.delete_suborg, name='index'),


    path('registration', views_admin.registration, name='index'),
    path('requestelement', views_admin.requestelement, name='index'),
    path('successrequest', views_admin.successrequest, name='index'), #нужно удалить
    path('notification', views_admin.notification, name='index'),
    path('update', views_admin.update, name='index'),
    path('transfer', views_admin.transfer, name='index'),
    path('visitforKazna', views_admin.visitforKazna, name='index'),
    path('visitforKaznaFullOrg', views_admin.visitforKaznaFullOrg, name='index'),
    path('tabelxls', views_admin.generetexlstabel, name='index'),
    path('formfordash', views_admin.formfordash, name='index'),
    path('formfordashsumm', views_admin.formfordashsumm, name='index'),
    path('getpriceservice', views_admin.getpriceservice, name='index'),
    path('getpriceobl', views_admin.getpriceobl, name='index'),
    path('setpriceobl', views_admin.setpriceobl, name='index'),
    path('getStatusRegion', views_admin.getStatusRegion, name='index'),    
    # path('formnovisit', views_admin.formnovisit, name='index'),
    

    path('getotherphoto', views_admin.getotherphoto, name='index'), 

]
