from django.db import models
import datetime
# from django.contrib.auth.models import User
# from django.db.models.signals import post_save
# from django.dispatch import receiver

class Childs(models.Model):
    iin = models.CharField(max_length=12)
    name = models.TextField(null=True, blank=True)
    birthday = models.DateField(null=True) 
    gender = models.TextField(null=True, blank=True)
    id_group = models.CharField(max_length=15)
    id_org = models.CharField(max_length=15)
    registered = models.BooleanField(default = False)
    child_image = models.TextField(null=True, default="")
    id_face = models.TextField(null=True, default="")
    is_delete = models.BooleanField(null=True, default = False)
    create_date = models.DateField(default=datetime.datetime.now(), blank=None, null=None) 


class Organizations(models.Model):
    id_org = models.CharField(max_length=15)
    org_name = models.TextField(null=True, blank=True)
    latitude = models.TextField(null=True, blank=True)
    longitude = models.TextField(null=True, blank=True)
    checkedgps = models.BooleanField(null=True, default = True)
    create_date = models.DateField(null=True, auto_now_add=True) 


class ProfileUser(models.Model):
    id_org = models.CharField(max_length=15)        #Код организации, соответствующий логину        
    name = models.TextField(null=True, blank=True)  #Логин пользователя
    is_adm_org = models.BooleanField(null=True, default = False)  #Это администратор садика (истина - да админ)
    create_date = models.DateField(null=True, auto_now_add=True) 
    is_delete = models.BooleanField(null=True, default = False)

class Groups(models.Model):
    id_group    = models.CharField(max_length=15)
    id_org      = models.CharField(max_length=15, default="00000")
    group_name  = models.TextField(null=True, blank=True)
    group_age   = models.TextField(null=True, blank=True) 
    group_count = models.IntegerField(default=0)
    is_delete = models.BooleanField(null=True, default = False)
    username    = models.TextField(null=True, blank=True) #Логин закрепленного воспитателя
    create_date = models.DateField(null=True, auto_now_add=True) 


class Visits(models.Model):
    id_group    = models.CharField(max_length=15)
    id_org      = models.CharField(max_length=15)
    iin         = models.CharField(max_length=15)
    # Нет регистрации - 0, Не посетил - 1, Посетил - 2, Больничный - 3, Отпуск - 4
    status      = models.CharField(max_length=15, default='0')  
    datestatus   = models.DateField(null=True) 
    timestatus   = models.TimeField(null=True)
    create_date = models.DateTimeField(default=datetime.datetime.now(), blank=None, null=None) 

