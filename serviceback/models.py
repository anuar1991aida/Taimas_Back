from django.db import models
import datetime
# from django.contrib.auth.models import User
# from django.db.models.signals import post_save
# from django.dispatch import receiver

class Childs(models.Model):
    iin = models.CharField(max_length=12, db_index=True)
    name = models.TextField(null=True, blank=True, db_index=True)
    birthday = models.DateField(null=True) 
    gender = models.TextField(null=True, blank=True)
    id_group = models.CharField(max_length=15, db_index=True)
    id_org = models.CharField(max_length=15, db_index=True)
    registered = models.BooleanField(default = False)
    image_url    = models.TextField(null=True, blank=True) #Адрес фото зарегистрированного
    icon_url    = models.TextField(null=True, blank=True) #Адрес иконки зарегистрированоого
    is_delete = models.BooleanField(null=True, default = False)
    category    = models.CharField(null=True, blank=True, max_length=5)
    create_date = models.DateField(blank=None, null=True) 
    clone = models.TextField(null=True, blank=True, db_index=True) #иин для близняшек
    # id_face = models.TextField(null=True, default="")
    # id_face512 = models.TextField(null=True, default="")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Дети'
        verbose_name = 'Ребенок'
        ordering = ['name']


class Descriptors(models.Model):
    iin = models.CharField(max_length=12, db_index=True)
    id_face128 = models.TextField(null=True, default="")
    id_face512 = models.TextField(null=True, default="")
    id_face1024 = models.TextField(null=True, default="")
    image_url    = models.TextField(null=True, blank=True)
    create_date = models.DateField(blank=None, null=True) 



class TelegramData(models.Model):
    iin = models.CharField(max_length=12, db_index=True)
    chatid = models.BigIntegerField(null=True)




class FakeCountByIIN(models.Model):
    iin = models.CharField(max_length=12, db_index=True)
    create_date = models.DateField(blank=None, null=True) 
    confidence = models.FloatField(null=True, default=0)
    count = models.IntegerField(null=True, default=0)


# class AntiSpoof(models.Model):
#     var1 = models.TextField(null=True, default="")
#     var2 = models.TextField(null=True, default="")
#     argmax1 = models.TextField(null=True, default="")
#     argmax2 = models.TextField(null=True, default="")
#     argmax = models.TextField(null=True, blank=True)
#     imagename = models.TextField(null=True, blank=True)
#     res = models.TextField(null=True, blank=True)



class Organizations(models.Model):
    id_obl = models.BigIntegerField(default=0) #id области с модели Regions
    id_region = models.BigIntegerField(default=0) #id региона с модели Regions
    id_org = models.CharField(max_length=15, db_index=True)
    org_name = models.TextField(null=True, blank=True, db_index=True)
    latitude = models.TextField(null=True, blank=True)
    longitude = models.TextField(null=True, blank=True)
    checkedgps = models.BooleanField(null=True, default = True)
    create_date = models.DateField(null=True, auto_now_add=True)  
    bin = models.TextField(max_length=12, default="", db_index=True)
    fullname = models.TextField(null=True, blank=True, db_index=True)
    phonenumber = models.TextField(null=True, blank=True)
    adress = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    count_place = models.BigIntegerField(default=0) # проектная мощность
    # тип организации pr - Частная, gs - Государственная
    type_org = models.CharField(max_length=3, default='pr')
    worktimestart  = models.TimeField(null=True)
    worktimestop  = models.TimeField(null=True)
    type_city = models.CharField(null=True, blank=True, max_length=4, default='gor')
    type_ecolog = models.CharField(null=True, blank=True, max_length=6, default='normal')

    def __str__(self):
        return self.org_name + ' ' + self.bin

    class Meta:
        verbose_name_plural = 'Организации'
        verbose_name = 'Организация'
        ordering = ['org_name']

class ProfileUser(models.Model):
    id_org = models.CharField(max_length=15, db_index=True)        #Код организации, соответствующий логину        
    name = models.TextField(null=True, blank=True, db_index=True)  #Логин пользователя
    is_adm_org = models.BooleanField(null=True, default = False)  #Это администратор садика (истина - да админ)
    create_date = models.DateField(null=True, auto_now_add=True) 
    is_pass_chek = models.BooleanField(null=True, default = False)
    is_delete = models.BooleanField(null=True, default = False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Пользователи'
        verbose_name = 'Пользователь'
        ordering = ['name']

class Groups(models.Model):
    id_group    = models.CharField(max_length=15, db_index=True)
    id_org      = models.CharField(max_length=15, default="00000", db_index=True)
    group_name  = models.TextField(null=True, blank=True)
    group_age   = models.TextField(null=True, blank=True) 
    group_count = models.IntegerField(null=True, blank=True, default=0)
    category    = models.CharField(null=True, blank=True, max_length=5)
    is_delete = models.BooleanField(null=True, default = False)
    username    = models.TextField(null=True, blank=True) #Логин закрепленного воспитателя
    create_date = models.DateField(null=True) 

    def __str__(self):
        return self.group_name + ' ' + self.id_org

    class Meta:
        verbose_name_plural = 'Группы'
        verbose_name = 'Группа'
        ordering = ['group_name']

class Visits(models.Model):
    id_group    = models.CharField(max_length=15, db_index=True)
    id_org      = models.CharField(max_length=15, db_index=True)
    iin         = models.CharField(max_length=15, db_index=True)
    # Нет регистрации - 0, Ожидает сканирования - 1, Посетил - 2, Больничный - 3, Отпуск - 4, Не посетил - 5, Лицо не расп - 6,  Ложное фото - 10, В обработке - 9
    status      = models.CharField(max_length=15, default='0')  
    username    = models.TextField(null=True, blank=True) #Логин воспитателя для фиксации
    datestatus  = models.DateField(null=True, db_index=True) 
    timestatus  = models.TimeField(null=True)
    image_url   = models.TextField(null=True, blank=True) #Адрес фото распознанного
    comments    = models.TextField(null=True, blank=True) #служебное
    srvcolumn   = models.TextField(null=True, blank=True) #Служебное поле
    edited      = models.BooleanField(default=False)
    fakeresult   = models.FloatField(default=1, null=True, blank=True)
    # hostname    = models.TextField(null=True, blank=True)
    # create_date = models.DateTimeField(default=datetime.datetime.now(), blank=None, null=None)


class Visits_faceme(models.Model):
    id_group    = models.CharField(max_length=15, db_index=True)
    id_org      = models.CharField(max_length=15, db_index=True)
    iin         = models.CharField(max_length=15, db_index=True)
    # Нет регистрации - 0, Ожидает сканирования - 1, Посетил - 2, Больничный - 3, Отпуск - 4, Не посетил - 5, Лицо не расп - 6,  Ложное фото - 10, В обработке - 9
    status      = models.CharField(max_length=15, default='0')  
    username    = models.TextField(null=True, blank=True) #Логин воспитателя для фиксации
    datestatus  = models.DateField(null=True, db_index=True) 
    timestatus  = models.TimeField(null=True)
    image_url   = models.TextField(null=True, blank=True) #Адрес фото распознанного
    comments    = models.TextField(null=True, blank=True) #служебное
    srvcolumn   = models.TextField(null=True, blank=True) #Служебное поле
    edited      = models.BooleanField(default=False)
    fakeresult   = models.FloatField(default=1, null=True, blank=True)
    # hostname    = models.TextField(null=True, blank=True)
    # create_date = models.DateTimeField(default=datetime.datetime.now(), blank=None, null=None)

class NewOrganizations(models.Model):
    id_obl = models.BigIntegerField(default=0) #id области с модели Regions
    id_region = models.BigIntegerField(default=0) #id региона с модели Regions
    bin = models.TextField(max_length=12, default="")
    org_name = models.TextField(null=True, blank=True)
    fullname = models.TextField(null=True, blank=True)
    phonenumber = models.TextField(null=True, blank=True)
    adress = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    password = models.TextField(null=True, blank=True)
    datestatus  = models.DateField(null=True) 
    latitude = models.TextField(null=True, blank=True)
    longitude = models.TextField(null=True, blank=True)
    # Новая заявка - 0, одобрено - 1, отказано - 2
    status = models.CharField(max_length=15, default='0') #статус заявки
    count_place = models.BigIntegerField(default=0) # проектная мощность
    # тип организации pr - Частная, gs - Государственная
    type_org = models.CharField(null=True, blank=True, max_length=3, default='gos')
    type_city = models.CharField(null=True, blank=True, max_length=4, default='gor')
    type_ecolog = models.CharField(null=True, blank=True, max_length=6, default='normal')
    
class SubOrganizations(models.Model):
    id_parent = models.CharField(max_length=15)
    id_child  = models.CharField(max_length=15) 

    class Meta:
        verbose_name_plural = 'Иерархия организаций'
        verbose_name = 'Организация'

class Regions(models.Model):
    name      = models.TextField(null=True, blank=True)
    id_parent = models.BigIntegerField(default=0)
    latitude = models.TextField(null=True, blank=True)
    longitude = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Регионы'
        verbose_name = 'Регион'
        ordering = ['name']

class PriceService(models.Model):
    obl = models.ForeignKey(Regions, on_delete=models.CASCADE)
    type_ecolog = models.CharField(null=True, blank=True, max_length=6, default='normal')
    type_city = models.CharField(null=True, blank=True, max_length=4, default='gor')
    category    = models.CharField(null=True, blank=True, max_length=5)
    price = models.BigIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Цены обслуживания'
        verbose_name = 'Организация'

class WeekendDay(models.Model):
    weekend  = models.DateField(null=True)
    name         = models.CharField(max_length=2)
    
    class Meta:
        verbose_name_plural = 'Выходные дни'
        verbose_name = 'Выходной день'

class ItogByDay(models.Model):
    datestatus = models.DateField(null=True, db_index=True)
    id_org     = models.CharField(max_length=15, db_index=True)
    visit      = models.IntegerField(default=0)
    boln       = models.IntegerField(default=0)
    otpusk     = models.IntegerField(default=0)
    notvisit   = models.IntegerField(default=0)

class ItogByMonth(models.Model):
    datestatus = models.DateField(null=True, db_index=True)
    id_org     = models.CharField(max_length=15, db_index=True)
    visit      = models.IntegerField(default=0)
    boln       = models.IntegerField(default=0)
    otpusk     = models.IntegerField(default=0)
    notvisit   = models.IntegerField(default=0)

class History(models.Model):
    id_org      = models.CharField(max_length=15, db_index=True)
    id_group    = models.CharField(max_length=15, db_index=True)
    iin         = models.CharField(max_length=15, db_index=True)
    date        = models.DateField(null=True, db_index=True)
    timestatus  = models.TimeField(null=True)
    # Принят - 1, Исключен - 2
    status      = models.CharField(max_length=1, default='1')    
    date_dir    = models.DateField(null=True, db_index=True)
    
    class Meta:
        verbose_name_plural = 'Истории ребенка'
        verbose_name = 'История ребенка'