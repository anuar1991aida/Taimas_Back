import base64
import io
from django.http import HttpResponse
from rest_framework.decorators import api_view
import datetime
import json
import requests
import os
from urllib3.exceptions import InsecureRequestWarning  # added
from .models import Childs, Organizations, Groups, Visits, ProfileUser
from django.db import connection
from django.contrib.auth.models import User
import xlrd
# import pandas as pd
# from openpyxl import Workbook
import struct

# *******************************************
# Системные функции для работы приложения
# *******************************************
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
basepath = '//192.168.5.22/FaceDastan'


def get_org_id(username):
    usrobj = ProfileUser.objects.all()
    usrobj = usrobj.filter(name=username)
    for itemorg in usrobj:
        id_org = itemorg.id_org
    return id_org


# Сервис для обновления данных в базе данных
@api_view(['POST'])
def updateChilds(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    # Структура должна быть как показано ниже
    datajson = """[
    {
        "org_name": "JSOFT",
        "id_org": 99999,
        "group_mass": [
            {
                "id_group": "10001716",
                "group_name": "АДМ",
                "child_mass": [
                    {
                        "child_name": "Акжигитова Индира Сансызбаевна",
                        "child_iin": "730101403130",
                        "child_present": "false",
                        "status": "",
                        "child_image": "child_image"
                    },
                    {
                        "child_name": "Ашимов Танат Канатович",
                        "child_iin": "910511301086",
                        "child_present": "false",
                        "status": "",
                        "child_image": "child_image"
                    }
                ]
            },
            {
                "id_group": "10001717",
                "group_name": "Методист",
                "child_mass": [
                    {
                        "child_name": "Аманжол Бексұлтан Батырханұлы",
                        "child_iin": "940910301873",
                        "child_present": "false",
                        "status": "",
                        "child_image": "child_image"
                    }
                ]
            }
        ]
    }
]"""

    # Получаем данные с тела запроса
    data = json.loads(request.body)
    for orgitem in data:
        id_org = orgitem['org_ID']
        org_name = orgitem['org_name']
        # Получаем имеющиеся данные с БД (таблица организации)
        findorg = Organizations.objects.all()
        # Фильтруем по коду организации
        findorg = findorg.filter(id_org=id_org)

        # Проверяем, есть ли в БД такая организация
        existorg = False
        for item in findorg:
            existorg = True
            break

        # Если нет, то создаем организацию, если есть, то ничего не делаем
        if existorg == False:
            itemOrg = Organizations(id_org=id_org, org_name=org_name)
            itemOrg.save()

        # Далее создаем рабочюю папку организации, если не было.
        path_org = basepath + '/Register/' + str(id_org)
        direxist = os.path.isdir(path_org)
        if not direxist:
            os.mkdir(path_org)

        # Получаем массив групп в запросе и также проверяем на существование
        groups = orgitem['group_mass']
        for itemgr in groups:
            id_group = itemgr['group_id']
            # Получаем из БД все группы и фильтруем по коду орг и группы
            findgroup = Groups.objects.all()
            findgroup = findgroup.filter(id_group=id_group)
            findgroup = findgroup.filter(id_org=id_org)

            # Проверим, есть ли такая группа
            existgr = False
            for item in findgroup:
                existgr = True
                break

            # Если нет в БД, то создаем группу
            if existgr == False:
                itemGr = Groups(id_group=id_group,
                                group_name=itemgr['group_name'], id_org=id_org)
                itemGr.save()

            # Если нет папки для группы, то создаем папку
            path_group = path_org + '/' + str(id_group)
            direxist = os.path.isdir(path_group)
            if not direxist:
                os.mkdir(path_group)

            # Получаем детей в группе из запроса
            childs = itemgr['child_mass']
            for itemch in childs:
                iin = itemch['child_iin']
                name = itemch['child_name']

                # Получаем детей в БД, фильтруем по орг, группе, и коду детей
                findchild = Childs.objects.all()
                findchild = findchild.filter(id_org=id_org)
                findchild = findchild.filter(id_group=id_group)
                findchild = findchild.filter(iin=iin)

                # Проверяем есть ли в БД ребенок с таким кодом
                existchild = False
                for item in findchild:
                    existchild = True
                    break

                # Если нет в БД, то создаем запись
                if existchild == False:
                    itemChld = Childs(id_group=id_group,
                                      id_org=id_org, iin=iin, name=name)
                    itemChld.save()

                # Если нет папки ребенка, то создаем папку (формат: С910114301692)
                path_child = path_group + '/C' + str(iin)
                direxist = os.path.isdir(path_child)
                if not direxist:
                    os.mkdir(path_child)

    return HttpResponse('{"status": "success"}', content_type="application/json")


# Сервис авторизациии пользователя. Если только админ флаг установлен в Истина
@api_view(['GET'])
def authuser(request):

    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    username = request.user
    usrobj = ProfileUser.objects.all()
    usrobj = usrobj.filter(name=username)

    for itemorg in usrobj:
        if not itemorg.is_adm_org:
            return HttpResponse('{"status": "Ошибка авторизации. Вы не администратор"}', content_type="application/json", status=401)
        id_org = itemorg.id_org

    query = """SELECT orgs.org_name
                FROM serviceback_organizations as orgs
                WHERE
                    orgs.id_org = %s"""

    with connection.cursor() as cursor:
        cursor.execute(query, [id_org])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result), content_type="application/json")


# Сервис получения списка воспитательных групп
@api_view(['GET'])
def grouplist(request):

    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    query = """SELECT groups.id_group, groups.group_name, groups.group_age, groups.group_count, users.first_name, users.last_name, users.username
                FROM serviceback_groups as groups
                LEFT JOIN auth_user AS users
                ON groups.username = users.username
                WHERE (NOT groups.is_delete) and (groups.id_org = %s)"""

    with connection.cursor() as cursor:
        cursor.execute(query, [id_org])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result), content_type="application/json")


# Сервис редактирования таблицы "Воспитательные группы"
@api_view(['POST'])
def groupedit(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    param = request.GET.get("param")
    datastr = request.body
    res = json.loads(datastr)

    if param == 'edit':
        for item in res:
            try:
                zapisgroup = Groups.objects.get(
                    id_group=item['id_group'], id_org=id_org)
                zapisgroup.group_name = item['group_name']
                zapisgroup.group_count = item['group_count']
                zapisgroup.group_age = item['group_age']
                zapisgroup.username = item['username']
                zapisgroup.save()
            except:
                return HttpResponse('{"status": "Ошибка редактирования группы."}', content_type="application/json", status=500)

    if param == 'add':
        try:
            zapisgroup = Groups.objects.get(group_name=item['group_name'], id_org=id_org)
            return HttpResponse('{"status": "Группа с таким названием уже существует."}', content_type="application/json", status=500)
        except:
            for item in res:
                zapisgroup = Groups()
                zapisgroup.group_name = item['group_name']
                zapisgroup.group_count = item['group_count']
                zapisgroup.group_age = item['group_age']
                zapisgroup.username = item['username']
                zapisgroup.id_org = id_org
                zapisgroup.save()
                zapisgroup.id_group = zapisgroup.id
                zapisgroup.save()

    if param == 'del':
        for item in res:
            zapischilds = Childs.objects.all()
            zapischilds = zapischilds.filter(
                id_org=id_org, id_group=item['id_group'])
            flag = False
            for itemchild in zapischilds:
                flag = True
                break

            if flag:
                return HttpResponse('{"status": "Ошибка удаления. В группе зарегистрированы дети."}', content_type="application/json", status=500)
            else:
                zapisgroup = Groups.objects.get(id_group=item['id_group'])
                zapisgroup.is_delete = True
                zapisgroup.save()

    query = """SELECT groups.id_group, groups.group_name, groups.group_age, groups.group_count, users.first_name, users.last_name, users.username
                FROM serviceback_groups as groups
                LEFT JOIN auth_user AS users
                ON groups.username = users.username
                WHERE (NOT groups.is_delete) and (groups.id_org = %s)"""

    with connection.cursor() as cursor:
        cursor.execute(query, [id_org])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]
    return HttpResponse(json.dumps(result), content_type="application/json")


# Сервис получения табеля для организации
@api_view(['GET'])
def gettabelbyday(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    datestatus = request.GET.get("datestatus")

    query = """SELECT id_group, iin, datestatus, status FROM serviceback_visits as visits
                WHERE
                    id_org = %s and datestatus = %s
                ORDER BY id_group
                """

    with connection.cursor() as cursor:
        cursor.execute(query, [id_org, datestatus])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result, indent=4, sort_keys=True, default=str), content_type="application/json")


# Сервис получения списка детей в группе
@api_view(['GET'])
def childlist(request):

    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    id_group = request.GET.get("id_group")
    childname = request.GET.get("childname")
    if id_group == None:
        id_group = ""
    if childname == None:
        childname = ""
    page = int(request.GET.get("page"))
    firstelement = (page-1) * 25
    lastelement = page * 25

    query = """SELECT childs.iin, childs.name, childs.id_group, groups.group_name
                FROM serviceback_childs as childs
                LEFT JOIN serviceback_groups as groups
                ON childs.id_group = groups.id_group and childs.id_org = groups.id_org
                WHERE (NOT childs.is_delete) and (childs.id_org = %s) and (childs.id_group LIKE %s)
                and (name LIKE %s)
                ORDER BY childs.iin"""

    with connection.cursor() as cursor:
        cursor.execute(
            query, [id_org, '%' + id_group + '%', '%' + childname + '%'])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]
        if lastelement > len(result):
            lastelement = len(result)
        res = {"list": result[firstelement:lastelement],
               "last": lastelement, "total": len(result)}

    return HttpResponse(json.dumps(res), content_type="application/json")


# Сервис получения списка детей в группе
@api_view(['GET'])
def getchildbyinn(request):

    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    id_group = request.GET.get("id_group")
    iin = request.GET.get("iin")

    query = """SELECT childs.iin, childs.name, to_char(childs.birthday,'dd.mm.yyyy') as birthday, childs.gender, childs.id_group, groups.group_name, childs.registered FROM serviceback_childs as childs
                LEFT JOIN serviceback_groups as groups
                ON childs.id_group = groups.id_group and childs.id_org = groups.id_org
                WHERE (NOT childs.is_delete) and (childs.id_org = %s) and (childs.id_group = %s) and (childs.iin = %s)"""

    with connection.cursor() as cursor:
        cursor.execute(query, [id_org, id_group, iin])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result), content_type="application/json")


# Сервис редактирования таблицы "Дети"
@api_view(['POST'])
def childedit(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    param = request.GET.get("param")
    id_group = request.GET.get("id_group")
    datastr = request.body
    res = json.loads(datastr)

    if param == 'edit':
        for item in res:
            try:
                zapischild = Childs.objects.all()
                zapischild = zapischild.filter(
                    id_org=id_org, id_group=id_group, iin=item['iin'], is_delete=False)
                for zap in zapischild:
                    zap.iin = item['iin']
                    zap.name = item['name']
                    birthday = item['birthday']
                    mass = birthday.split('.')
                    datarojd = datetime.date(
                        int(mass[2]), int(mass[1]), int(mass[0]))
                    zap.birthday = datarojd
                    zap.gender = item['gender']
                    zap.id_group = item['id_group']
                    zap.save()
            except:
                return HttpResponse('{"status": "Ошибка редактирования ребёнка."}', content_type="application/json", status=500)

    if param == 'add':
        for item in res:
            check = Childs.objects.all()
            check = check.filter(is_delete=False, iin=item['iin'])
            flagcheck = True
            for itemcheck in check:
                flagcheck = False
            if not flagcheck:
                return HttpResponse('{"status": "Ошибка добавления. Данный ребенок уже зарегистрирован."}', content_type="application/json", status=500)

            zapischild = Childs()
            zapischild.iin = item['iin']
            zapischild.name = item['name']
            zapischild.gender = item['gender']
            birthday = item['birthday']
            mass = birthday.split('.')
            datarojd = datetime.date(int(mass[2]), int(mass[1]), int(mass[0]))
            zapischild.birthday = datarojd
            zapischild.id_org = id_org
            zapischild.id_group = item['id_group']
            zapischild.registered = False
            zapischild.is_delete = False
            zapischild.save()

    if param == 'del':
        for item in res:
            zapischild = Childs.objects.all()
            zapischild = zapischild.filter(iin=item['iin'], is_delete=False)
            for checkitem in zapischild:
                checkitem.is_delete = True
                checkitem.save()

    query = """SELECT childs.iin, name, childs.id_group, childs.registered, groups.group_name
                FROM serviceback_childs as childs
                LEFT JOIN serviceback_groups as groups
                ON childs.id_group = groups.id_group and childs.id_org = groups.id_org
                WHERE (NOT childs.is_delete) and (childs.id_org = %s)"""

    with connection.cursor() as cursor:
        cursor.execute(query, [id_org])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]
    return HttpResponse(json.dumps(result), content_type="application/json")


# Сервис получения списка воспитателей
@api_view(['GET'])
def metodistlist(request):

    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)
    metodist = request.GET.get("metodist")
    if metodist == None:
        metodist = ''
    id_org = get_org_id(request.user)

    page = int(request.GET.get("page"))
    firstelement = (page-1) * 50
    lastelement = page * 50

    query = f"""SELECT profile.name as username, users.first_name, users.email
                FROM serviceback_profileuser as profile
                LEFT JOIN auth_user AS users
                ON profile.name = users.username
                WHERE (profile.id_org = '{id_org}') and (profile.is_delete=False)
                and (users.first_name like %s)
                order by users.first_name"""

    with connection.cursor() as cursor:
        cursor.execute(query, ['%'+metodist+'%'])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]
        if lastelement > len(result):
            lastelement = len(result)
        res = {"list": result[firstelement:lastelement],
               "last": lastelement, "total": len(result)}

    return HttpResponse(json.dumps(res), content_type="application/json")


# Сервис редактирования таблицы "Дети"
@api_view(['POST'])
def metodistedit(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    param = request.GET.get("param")
    datastr = request.body
    res = json.loads(datastr)

    if param == 'add':
        try:
            User.objects.create_user(
                username=res['username'],
                password=res['password'],
                email=res['email'],
                first_name=res['first_name'])
            # last_name =  res['last_name'])

            profile = ProfileUser()
            profile.id_org = id_org
            profile.is_adm_org = False
            profile.name = res['username']
            profile.save()

            return HttpResponse('{"status": "Успешно добавлен логин"}', content_type="application/json", status=200)
        except:
            return HttpResponse('{"status": "Ошибка добавления. Данный Логин уже зарегистрирован."}', content_type="application/json", status=500)

    if param == 'del':
        try:
            u = User.objects.get(username=res['username'])
            u.delete()
            profile = ProfileUser.objects.all()
            profile = profile.filter(name=res['username'])
            for itemprofile in profile:
                itemprofile.is_delete = True
                itemprofile.save()

        except User.DoesNotExist:
            return HttpResponse('{"status": "Ошибка удаления пользователя"}', content_type="application/json", status=500)

    if param == 'changepass':
        try:
            u = User.objects.get(username=res['username'])
            u.set_password(res['password'])
            u.save()
        except User.DoesNotExist:
            return HttpResponse('{"status": "Ошибка изменения пароля"}', content_type="application/json", status=500)

    return HttpResponse('{"status": "Успешно."}', content_type="application/json", status=200)


@api_view(['POST'])
def importfile(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    datastr = request.body
    res = json.loads(datastr)
    fileres = res['file']
    fileres = fileres.replace(
        "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,", "")

    excel_data = base64.b64decode(fileres)
    path = '//192.168.5.17/ssd/temp/' + id_org + '.xls'
    with open(path, 'wb+') as destination:
        destination.write(excel_data)
    workbook = xlrd.open_workbook(path)
    worksheet = workbook.sheet_by_index(0)
    nrows = worksheet.nrows

    try:
        for i in range(1, nrows):
            check = Childs.objects.all()
            check = check.filter(is_delete=False, iin=worksheet.cell_value(i, 2))
            flagcheck = True
            for itemcheck in check:
                flagcheck = False
            if flagcheck:
                zapischild = Childs()
                zapischild.iin = worksheet.cell_value(i, 2)
                zapischild.name = worksheet.cell_value(
                    i, 3) + ' ' + worksheet.cell_value(i, 4) + ' ' + worksheet.cell_value(i, 5)

                if zapischild.iin[6] == '5':
                    zapischild.gender = 'm'
                else:
                    zapischild.gender = 'w'
                datarojd = datetime.date(int(
                    '2000') + int(zapischild.iin[:2]), int(zapischild.iin[2:4]), int(zapischild.iin[4:6]))
                zapischild.birthday = datarojd
                zapischild.id_org = id_org
                zapischild.registered = False
                zapischild.is_delete = False
                try:
                    zapisgroup = Groups.objects.get(
                        group_name=worksheet.cell_value(i, 23), id_org=id_org)
                except:
                    zapisgroup = Groups()
                    zapisgroup.group_name = worksheet.cell_value(i, 23)
                    zapisgroup.group_count = 0
                    zapisgroup.group_age = 1
                    zapisgroup.id_org = id_org
                    zapisgroup.save()
                    zapisgroup.id_group = zapisgroup.id
                    zapisgroup.save()
                zapischild.id_group = zapisgroup.id_group
                zapischild.save()

        return HttpResponse('{"status": "Данные детей успешно загружены"}', content_type="application/json", status=200)
    except:
        return HttpResponse('{"status": "Ошибка добавления. Некорректные данные."}', content_type="application/json", status=500)

    # return HttpResponse('{"status": "Успешно."}', content_type="application/json", status=200)

@api_view(['GET'])
def startpage(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)
    
    id_org = get_org_id(request.user)

    query = f"""with count_gr as(SELECT count(*) as quantityofgroup from public.serviceback_groups
                where id_org = '{id_org}' and is_delete = false),
                count_child as(SELECT count(*) as quantityofchild from public.serviceback_childs
                where id_org = '{id_org}' and is_delete = false),
                count_metodist as(SELECT count(*) as quantityofmetodist from public.serviceback_profileuser
                where id_org = '{id_org}' and is_delete = false)
                select count_gr.quantityofgroup, count_child.quantityofchild,
                count_metodist.quantityofmetodist from count_gr, count_child, count_metodist"""

    with connection.cursor() as cursor:
        cursor.execute(query, [id_org])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result), content_type="application/json")