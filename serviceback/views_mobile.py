from django.http import HttpResponse
from rest_framework.decorators import api_view,permission_classes
import os
import datetime
import base64
import json
import requests
from time import time
from django.utils import timezone
from PIL import Image  # pip install Pillow
from urllib3.exceptions import InsecureRequestWarning  # added
from .models import Childs, Visits, ProfileUser, Descriptors, FakeCountByIIN, TelegramData
from django.db import connection, transaction
import numpy as np
from scipy.spatial.distance import cosine
from django.core.serializers.json import DjangoJSONEncoder
from typing import List, Dict, Any, Tuple
import math
from rest_framework.permissions import IsAuthenticated
import telebot
import pandas as pd
import threading

# *******************************************
# Системные функции для работы приложения
# *******************************************
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
basepath = '//192.168.5.29/QaznaFace/'


def get_org_id(username):
    id_org = ''
    usrobj = ProfileUser.objects.all()
    usrobj = usrobj.filter(name=username)
    for itemorg in usrobj:
        id_org = itemorg.id_org
    return id_org


def statusfromDB(id_org, id_group, status="all"):
    filter = "('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10')"
    if status == None:
        filter = "('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10')"
    if status == 'waiting':
        filter = "('0', '1', '10')"
    if status == 'boln':
        filter = "('3')"
    if status == 'otp':
        filter = "('4')"
    if status == 'notvis':
        filter = "('5')"

    query = f"""
                WITH
                    childs as ( select id_org, id_group, iin, registered, image_url, icon_url, name, category from serviceback_childs
                                where id_org = '{id_org}' and not is_delete and id_group='{id_group}' 
                                ),
                    visit as (
                        select * from serviceback_visits
                        where id_org = '{id_org}' and id_group = '{id_group}' and datestatus = '{datetime.date.today()}'),
                    tmptbl as (select iin, max(id) as id from visit
                        group by iin),
                    resvisit as (
                        select visit.* from visit
                        where (iin, id) in (select iin, id from tmptbl)
                    ),
                    itogtable as (
                        SELECT
                        childs.iin,
                        replace(childs.image_url, 'FilesArchiv', 'https://face11.qazna24.kz/media') as image_url,
                        replace(childs.icon_url, 'FilesArchiv', 'https://face11.qazna24.kz/media') as icon_url,
                        childs.name,
                        CASE
                            
                            WHEN NOT childs.registered THEN '0'
                            WHEN visits.status IS NULL  THEN '1'
                            ELSE visits.status
                        END as status,
                        CASE
                            WHEN childs.category = 'gork' THEN 'Особенный ребенок'
                            WHEN NOT childs.registered and visits.status IS NULL THEN 'Первичная идентификация'
                            WHEN visits.status IS NULL or visits.status = '1'  THEN 'Ожидают сканирования'
                            WHEN visits.status = '2'    THEN  TO_CHAR(visits.timestatus, 'HH24:MI:SS')
                            WHEN visits.status = '3'    THEN 'Больничный'
                            WHEN visits.status = '4'    THEN 'Отпуск'
                            WHEN visits.status = '5'    THEN 'Отсутствует'
                            WHEN visits.status = '6'    THEN 'Лицо не распознано'
                            WHEN visits.status = '9'    THEN 'Отправлен в обработку'
                            WHEN visits.status = '10' and  visits.comments is null  THEN 'Фото проверяется. Ожидайте результата!'
                            WHEN visits.status = '10' and  not visits.comments is null  THEN 'Ложное фото. Действие зафиксировано!'
                            ELSE 'Статус не определен'
                        END as statusname,
                        childs.category
                        FROM childs
                        LEFT JOIN resvisit as visits ON
                            visits.iin = childs.iin)
                    SELECT * FROM itogtable
                    WHERE status in {filter}
                    ORDER BY name
                """

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        resultchild = [dict(zip(columns, row))
               for row in cursor.fetchall()]


    grstat = []
    grstat.append({
            "notreg": 0,
            "notvis": 0,
            "waiting": 0,
            "vis": 0,
            "boln": 0,
            "otp": 0,
            "cheked": 0,
            "common": 0
        })

    result = {"groupstatus": grstat, "childstatus": resultchild}
    return result


@api_view(['POST', 'GET'])
def setstatus(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)
    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    iin = request.GET.get("iin")
    status = request.GET.get("status")
    filterstatus = request.GET.get("filterstatus")
    

    if status == '2':
        child = Childs.objects.filter(id_org = id_org, id_group = id_group, iin = iin, is_delete = False)
        isGORK = True
        for itmch in child:
            if not itmch.category == 'gork':
                isGORK = False
            else:
                if itmch.registered == False:
                    itmch.registered = True
                    itmch.save()

        
        if isGORK:
            itemGr = Visits(id_group=id_group,
                    id_org=id_org,
                    iin=iin,
                    status=status,
                    username=username,
                    datestatus=datetime.datetime.today(),
                    timestatus=datetime.datetime.now(),
                    edited=False
                    )
            itemGr.save()
        else:
            return HttpResponse('{"status": "Запрет установки статуса посещения."}', content_type="application/json", status=400)

    elif status == '4':
        query = f"""
                with allvisbyiin as (
                    SELECT
                        id, 
                        status, 
                        datestatus 
                    FROM 
                        public.serviceback_visits 
                    where 
                        id_group='{id_group}' 
                        and id_org = '{id_org}' 
                        and iin='{iin}'),
                    maxidvis as (
                    select 
                        max(id) as id, 
                        datestatus 
                    from 
                        allvisbyiin 
                    group by 
                        datestatus),
                    resvis as (
                    select 
                        * 
                    from 
                        allvisbyiin 
                    where 
                        id in (
                            select 
                                id 
                            from 
                                maxidvis))
                    select 
                        * 
                    from 
                        resvis
                    where 
                        status='4'"""
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            queryres = [dict(zip(columns, row))
                for row in cursor.fetchall()]
            
            if len(queryres)>=60:
                return HttpResponse('{"status": "Превышен лимит отпуска на этот год!"}', content_type="application/json", status=400)
            else:
                itemGr = Visits(id_group=id_group,
                        id_org=id_org,
                        iin=iin,
                        status='4',
                        username=username,
                        datestatus=datetime.datetime.today(),
                        timestatus=datetime.datetime.now(),
                        edited=False)
                itemGr.save()

                try:
                    chats = TelegramData.objects.get(iin=iin)
                    token = '6677571095:AAFEpbRyIAPXHvVg6sLttUYPZeOryYqvAe8'
                    bot = telebot.TeleBot(token)
                    chatId = chats.chatid
                    send= 'Вас ребенок отмечен как в отпуске: '+str(iin) + ' в ' + str(datetime.date.today())
                    bot.send_message(chatId, send)
                except:
                    a = 1

    else:
        itemGr = Visits(id_group=id_group,
                        id_org=id_org,
                        iin=iin,
                        status=status,
                        username=username,
                        datestatus=datetime.datetime.today(),
                        timestatus=datetime.datetime.now(),
                        edited=False
                        )
        itemGr.save()

        if status == '3':
            try:
                chats = TelegramData.objects.get(iin=iin)
                token = '6677571095:AAFEpbRyIAPXHvVg6sLttUYPZeOryYqvAe8'
                bot = telebot.TeleBot(token)
                chatId = chats.chatid
                send= 'Вас ребенок отмечен как на больничном: '+str(iin) + ' в ' + str(datetime.date.today())
                bot.send_message(chatId, send)
            except:
                a = 1
    
    
    result = statusfromDB(id_org, id_group, filterstatus)
    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['POST', 'GET'])
def authuser(request):

    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    username = request.user
    # id_org = get_org_id(username)

    query = f"""SELECT
                    users.username,
                    users.first_name,
                    users.last_name,
                    profile.id_org,
                    orgs.org_name,
                    orgs.latitude,
                    orgs.longitude,
                    TO_CHAR(orgs.worktimestart, 'HH24:MI:SS') as worktimestart,
                    TO_CHAR(orgs.worktimestop, 'HH24:MI:SS') as worktimestop,
                    CASE
                        WHEN '{datetime.datetime.now()}' BETWEEN  orgs.worktimestart and orgs.worktimestop  THEN false
                        ELSE true
                    END as errortime,
                    orgs.checkedgps,
                    0.5 as distGPS
                FROM auth_user as users
                LEFT JOIN serviceback_profileuser AS profile ON
                    profile.name = users.username
                LEFT JOIN serviceback_organizations AS orgs ON
                    orgs.id_org = profile.id_org
                WHERE
                    users.username = '{username}'"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
               for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result, cls=DjangoJSONEncoder), content_type="application/json")


@api_view(['GET'])
def groupstatus(request):
    username = request.user
    id_org = get_org_id(username)

    query = f"""WITH
                    groups as ( select id_org, id_group, group_name from serviceback_groups
                                where id_org = '{id_org}' and not is_delete and username = '{username}'
                                ),
                    visit as (select id, id_group, id_org, iin, username, status from serviceback_visits
                                where id_org = '{id_org}' and datestatus = '{datetime.date.today()}'
                                      and id_group in (select id_group from groups)    
                                ),
                    tmptbl as (select iin, max(id) as id from visit
                                group by iin),
                    resvisit as (
                                select * from visit
                                where (iin, id) in (select iin, id from tmptbl)
                                ),
                    childs as ( select id_org, id_group, iin, registered from serviceback_childs
                                where id_org = '{id_org}' and not is_delete and id_group in (select id_group from groups) 
                                ),
                    

					statustable as (SELECT
                                    childs.id_group,
                                    childs.iin,
                                    CASE
                                        WHEN NOT childs.registered  THEN '0'
                                        WHEN visits.status IS NULL  THEN '1'
                                        ELSE visits.status
                                    END as status
                                FROM childs
                                LEFT JOIN resvisit as visits ON
                                    visits.id_org = childs.id_org
                                    and visits.id_group = childs.id_group
                                    and visits.iin = childs.iin),
                    groupstatus as (SELECT
                                    groupstbl.id_group,
                                    groupstbl.id_org,
                                    groupstbl.group_name,
                                    CASE
                                        WHEN statustable.status = '0'  THEN 1
                                        ELSE 0
                                    END as notregister,
                                    CASE
                                        WHEN statustable.status = '1'  THEN 1
                                        ELSE 0
                                    END as waiting,
                                    CASE
                                        WHEN statustable.status = '2'  THEN 1
                                        ELSE 0
                                    END as visited,
                                    CASE
                                        WHEN statustable.status = '3'  THEN 1
                                        ELSE 0
                                    END as bolnich,
                                    CASE
                                        WHEN statustable.status = '4'  THEN 1
                                        ELSE 0
                                    END as otpusk,
                                    CASE
                                        WHEN statustable.status in ('5', '10')  THEN 1
                                        ELSE 0
                                    END as notvisited,
                                    CASE
                                        WHEN statustable.status in ('2','3','4', '5', '9','10')  THEN 1
                                        ELSE 0
                                    END as checked,
                                    statustable.status as common
                                FROM groups as groupstbl
                                LEFT JOIN statustable ON
                                        groupstbl.id_group = statustable.id_group)

                    select id_group, id_org, group_name,
                            sum(notregister) as notreg,
                            sum(notvisited) as notvis,
                            sum(waiting) as waiting,
                            sum(visited) as vis,
                            sum(bolnich) as boln,
                            sum(otpusk) as otp,
                            sum(checked) as cheked,
                            count(common) as common from groupstatus
                    group by (id_group, id_org, group_name)"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
               for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['GET'])
def getdescriptors(request):
    username = request.user
    iin = request.GET.get("iin")

    query = f"""select id_face128 from serviceback_descriptors
                where iin = '{iin}'  and not id_face128 = '' """

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
               for row in cursor.fetchall()]

    mass_desc = []
    for row in result:
        Description = list(eval(row['id_face128']).values())
        mass_desc.append(Description)

    if len(mass_desc) == 0:
        return HttpResponse('{"status": "Не зарегистрированое лицо."}', content_type="application/json", status=401)
    else:
        res = {"descs": mass_desc, 
                "dist":0.27,
                "cnf_fapi": 0.65}
        return HttpResponse(json.dumps(res), content_type="application/json")



@api_view(['GET'])
def testdesc(request):
    # Укажите путь к файлу Excel
    excel_file = '123.xls'  # Замените на свой путь

    # Чтение данных из файла Excel
    df = pd.read_excel(excel_file)

    # Преобразование данных в HTML-таблицу
    html_table = df.to_html(header=False, index=False)
    # Создание HTML-файла и запись таблицы в него
    with open('output.html', 'w', encoding='utf-8') as html_file:
        html_file.write(html_table)
    return HttpResponse('{"status": "Зарегистрированое лицо."}', content_type="application/json")
    


@api_view(['GET'])
def childstatus(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    id_org = get_org_id(request.user)
    id_group = request.GET.get("id_group")
    filterstatus = request.GET.get("filterstatus")
    result = statusfromDB(id_org, id_group, filterstatus)
    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['GET'])
def childphoto(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    iin = request.GET.get("iin")

    # childobj = Childs.objects.all()
    childobj = Childs.objects.filter(id_org=id_org, id_group=id_group, iin=iin, is_delete = False)
    image_url = ''
    # encoded_string = ""

    try:
        for item in childobj:
            image_url = item.image_url
            image_url = image_url.replace(
                "FilesArchiv", "https://face11.qazna24.kz/media")
        return HttpResponse(json.dumps([{"image": image_url}]), content_type="application/json", status=200)

        # with open(image_url, "rb") as image_file:
        #         encoded_string = base64.b64encode(image_file.read())
        # resp = {'image': encoded_string.decode("utf-8")}
        # return HttpResponse(json.dumps(resp, indent=2), content_type="application/json")
    except:
        return HttpResponse({"status": "error"}, content_type="application/json", status=500)


@api_view(['GET'])
def childhistory(request):
    # if request.user.is_anonymous:
    return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=200)

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    iin = request.GET.get("iin")
    query = """SELECT datestatus, status, timestatus FROM serviceback_visits as visits
                WHERE
                    visits.id_org = %s and visits.id_group = %s
                    and visits.iin = %s
                ORDER BY visits.datestatus DESC
                LIMIT 30
                """

    with connection.cursor() as cursor:
        cursor.execute(query, [id_org, id_group, iin])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
               for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result, indent=4, sort_keys=True, default=str), content_type="application/json")


@api_view(['POST'])
def register(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    iin = request.GET.get("iin")
    datastr = request.body
    res = json.loads(datastr)
    detects = res['detects']

    dataphoto = str(datetime.datetime.today())
    dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
    path = 'FilesArchiv/Register/' + id_org + '_' + id_group + '_' + iin + '_'+ dataphoto + '.jpg'
    with open(basepath + path, 'wb+') as destination:
        imageelem = base64.b64decode(res['image'])
        destination.write(imageelem)

    im = Image.open(basepath + path)
    box = res['box']
    im_crop = im.crop((box['_x'], box['_y'], box['_x'] + box['_width'], box['_y'] + box['_height']))
    pathface = 'FilesArchiv/Icons/' + iin + '_' + dataphoto + '.jpg'
    im_crop.save(basepath + pathface, quality=5)

    childsBase = Childs.objects.filter(id_group = id_group, id_org = id_org, iin = iin, is_delete = False, registered = False)
    for itmchld in childsBase:
        itmchld.image_url = path
        itmchld.icon_url = pathface
        itmchld.registered = True
        itmchld.save()

    for itmdesc in detects:
        newdesc = Descriptors()
        newdesc.iin = iin
        newdesc.id_face128 = str(itmdesc)
        newdesc.image_url = path
        newdesc.create_date = datetime.datetime.now()
        newdesc.save()

    
    request_thread = threading.Thread(target=send_async_request, args=(id_org,id_group,iin,path))
    request_thread.start()

    return HttpResponse('{"status": "Успешная регистрация"}', content_type="application/json", status=200)


def send_async_request(id_org,id_group,iin,path):
    url = 'http://192.168.5.22:3000/register'  # Замените URL на целевой
    
    try:
        
        data ={
        'id_org': id_org,
        'id_group': id_group,
        'iin': iin,
        'path': path
        }

        response = requests.post(url, json=data)
        response.raise_for_status()  # Проверка на ошибки при запросе
        # Обработка ответа, если это необходимо
    except Exception as e:
        print(f'Ошибка при отправке запроса: {str(e)}')




def return_euclidean_distance(feature_1, feature_2):
        feature_1 = np.array(feature_1)
        feature_2 = np.array(feature_2)
        dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
        return dist


def cosine_similarity(vector1, vector2):
    dot_product = np.dot(vector1, vector2)
    magnitude1 = np.linalg.norm(vector1)
    magnitude2 = np.linalg.norm(vector2)
    similarity = dot_product / (magnitude1 * magnitude2)
    return similarity


@api_view(['POST'])
def sendphotogroup(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    return HttpResponse('{"status": "Обновите приложение из Play market. У Вас устаревшая версия Taimas!"}', content_type="application/json", status = 400) 

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    iin = request.GET.get("iin")
    resFake = request.GET.get("resFake")
    filterstatus = request.GET.get("filterstatus")
    datastr = request.body
    res = json.loads(datastr)
    try:
        image_data = base64.b64decode(res['image'][0])
    except:
        image_data = base64.b64decode(res['image'])
    detects = res['detects']

    isReal = True

    children_list = ''
    massiin = ""
    if 1 > 0:
        face_name_known_list = []
        face_feature_known_list = []
        if iin == None:
            query = """SELECT id_face,iin From serviceback_childs
                        WHERE
                            id_org = %s and id_group = %s and not id_face ='' and not is_delete
                    """

            query = f"""WITH childface as (SELECT id_face,iin From serviceback_childs
                                            WHERE id_org = '{id_org}' and id_group = '{id_group}' and not id_face ='' and not is_delete),
                            visits as (SELECT iin From serviceback_visits where datestatus='{datetime.date.today()}' and id_org = '{id_org}' and id_group = '{id_group}' and status='2')
                        select * from childface
                        where not iin in (select iin from visits)"""
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                for row in result:
                    features_someone_arr = []
                    face_name_known_list.append(row[1])
                    raz = row[0].split()
                    for z in raz:
                        s = z.strip()
                        features_someone_arr.append(float(s))
                    face_feature_known_list.append(features_someone_arr)
        else:
            query = """SELECT id_face,iin From serviceback_childs
                    WHERE
                        id_org = %s and id_group = %s and iin = %s;
                """
            with connection.cursor() as cursor:
                cursor.execute(query, [id_org, id_group, iin])
                result = cursor.fetchall()
                for row in result:
                    features_someone_arr = []
                    face_name_known_list.append(row[1])
                    raz = row[0].split()
                    for z in raz:
                        s = z.strip()
                        features_someone_arr.append(float(s))
                    face_feature_known_list.append(features_someone_arr)

        if len(face_feature_known_list) > 0:

            current_frame_face_feature_list = []
            current_frame_face_name_list = []

            if 1 != 0:
                # for itemdet in detects:

                descriptor = detects['descriptor']
                mass = []
                for i in range(128):
                    mass.append(descriptor[str(i)])
                current_frame_face_feature_list.append(mass)

            for k in range(1):
                current_frame_face_name_list.append("unknown")
                current_frame_e_distance_list = []
                for i in range(len(face_feature_known_list)):
                    if len(face_feature_known_list[i]) > 0:
                        if str(face_feature_known_list[i][0]) != '0.0':
                            e_distance_tmp = cosine(
                                current_frame_face_feature_list[k], face_feature_known_list[i])
                            current_frame_e_distance_list.append(
                                e_distance_tmp)
                        else:
                            current_frame_e_distance_list.append(999999999)
                    else:
                        current_frame_e_distance_list.append(999999999)

                similar_person_num = current_frame_e_distance_list.index(
                    min(current_frame_e_distance_list))
                if min(current_frame_e_distance_list) < 0.04:
                    current_frame_face_name_list[k] = face_name_known_list[similar_person_num]

                children_list = ''

                if len(current_frame_face_name_list) >= 1:
                    for i in current_frame_face_name_list:
                        if i == 'unknown':
                            continue
                        else:
                            stat = 2
                            dataphoto = str(datetime.datetime.today())
                            dataphoto = dataphoto.replace(
                                '-', '').replace(':', '').replace('.', '').replace(' ', '')
                            path = 'FilesArchiv/Recogn/' + id_org + '_' + id_group + \
                                '_' + i + '_' + \
                                    str(username) + '_' + dataphoto + '.jpg'
                            try:
                                with open(basepath + path, 'wb+') as destination:
                                    destination.write(image_data)
                            except:
                                print('error save picture to server')

                            # try:
                            #     box = detects['detection']['_box']
                            #     payload = {
                            #         'image_name': id_org + '_' + id_group + '_' + i + '_' + str(username) + '_' + dataphoto +'.jpg',
                            #         'box': box,
                            #         'id_org': id_org,
                            #         'id_group': id_group,
                            #         'iin': i,
                            #         'username': str(username),
                            #         'tip': 'recogn'
                            #     }
                            #     requests.post('http://192.168.5.15/filter_fake', json = payload, timeout = 2)
                            # except:
                            #     print('error server filter')

                            visit = Visits()
                            visit.id_org = id_org
                            visit.id_group = id_group
                            visit.iin = i
                            if isReal:
                                visit.status = 2
                            else:
                                visit.status = 10

                            # if resFake == 'Real':
                            # visit.status      = 9
                            # else:
                            #     visit.status      = 10
                            visit.datestatus = datetime.date.today()
                            visit.timestatus = datetime.datetime.now()
                            visit.username = username
                            visit.image_url = path
                            visit.comments = str(
                                min(current_frame_e_distance_list))
                            visit.edited = False
                            visit.save()
                            if massiin == "":
                                massiin = "'" + i + "'"
                            else:
                                massiin = massiin + ', ' + "'" + i + "'"
                            children_list = children_list + '-' + i

    result = statusfromDB(id_org, id_group, filterstatus)
    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['POST'])
def register512(request):
    global i
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status=401)

    return HttpResponse('{"status": "Обновите приложение из Play market. У Вас устаревшая версия Taimas!"}', content_type="application/json", status = 400) 

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    child_id = request.GET.get("iin")
    filterstatus = request.GET.get("filterstatus")
    datastr = request.body
    res = json.loads(datastr)
    mass_desciptor = res['descriptor']
    mass_image = res['image']
    box = res['box']

    dataphoto = str(datetime.datetime.today())
    dataphoto = dataphoto.replace(
        '-', '').replace(':', '').replace('.', '').replace(' ', '')
    descs = Descriptors.objects.filter(iin=child_id)
    for desc in descs:
        desc.delete()

    i = 0
    for desc in mass_desciptor:
        i = i + 1
        path = 'FilesArchiv/Register/' + id_org + '_' + id_group + '_' + child_id + '_' + dataphoto + str(i) + '.jpg'
        with open(basepath + path, 'wb+') as destination:
            try:
                imageelem = base64.b64decode(mass_image[i-1][0])
                destination.write(imageelem)
            except:
                asd = 1

        im = Image.open(basepath + path)
        boxx = box['data']
        im_crop = im.crop((boxx['0'], boxx['1'], boxx['2'], boxx['3']))
        pathface = 'FilesArchiv/Icons/' + child_id + '_' + dataphoto + '.jpg'
        im_crop.save(basepath + pathface, quality=5)

        newdesc = Descriptors()
        newdesc.iin = child_id
        newdesc.id_face512 = desc
        newdesc.image_url = path
        newdesc.create_date = datetime.datetime.now()
        newdesc.save()

        childobj = Childs.objects.filter(
            id_org=id_org, id_group=id_group, iin=child_id)
        for item in childobj:
            item.registered = True
            item.image_url = path
            item.icon_url = pathface
            item.save()

        # try:
        #     asd = 1
        #     payload = {
        #         'image_name': id_org + '_' + id_group + '_' + child_id + '_' + dataphoto + str(i) + '.jpg',
        #                     'id_org': id_org,
        #                     'id_group': id_group,
        #                     'iin': child_id,
        #                     'username': str(username),
        #                     'tip': 'registr'
        #                     }
        #     requests.post('http://192.168.5.15/filter_fake',
        #                   json=payload, timeout=2)
        # except:
        #     a = 1

    result = statusfromDB(id_org, id_group, filterstatus)
    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['POST'])
def sendphoto512(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)

    qset = Descriptors.objects.filter(iin='970415301144').order_by('-id')
    cnt = 0
    for itm in qset:
        cnt = cnt + 1
        if cnt == 1:
            baseDesc = list(eval(itm.id_face128).values())
        
        if cnt >=2:
            curDesc = list(eval(itm.id_face128).values())
            dist = return_euclidean_distance(baseDesc, curDesc)
            print(dist)

    return HttpResponse('{"status": "Обновите приложение из Play market. У Вас устаревшая версия Taimas!"}', content_type="application/json", status = 400) 
    
    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    filterstatus = request.GET.get("filterstatus")
    datastr = request.body
    res = json.loads(datastr)

    descriptor = res['descriptor']
    image_data = base64.b64decode(res['image'][0])


    if 1 > 0:
        face_name_known_list = []
        face_feature_known_list = []
  
        query = f"""with chlds as (SELECT iin From serviceback_childs 
                                    WHERE 
                                        id_org = '{id_org}' and id_group = '{id_group}' and registered and not is_delete
                                    order by name),
	                    vsts as (select iin from serviceback_visits
			                    where status = '2' and datestatus = '{datetime.date.today()}' and id_org = '{id_org}' and id_group = '{id_group}') 
                    select id_face512, iin from serviceback_descriptors
                            where iin in (select * from chlds) and not iin in (select * from vsts) and not id_face512=''
                            """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [id_org, id_group])
            result = cursor.fetchall()

            for row in result:
                features_someone_arr = []
                face_name_known_list.append(row[1])
                try:
                    myobj = eval(row[0])
                    mass_desc = list(myobj.values())
                    features_someone_arr.append(mass_desc)
                    face_feature_known_list.append(features_someone_arr)
                except:
                    a = 1
 

        if len(face_feature_known_list) > 0: 
            
            current_frame_face_feature_list = []
            current_frame_face_name_list = []
            current_frame_face_name_list2 = []

            # descriptor = detects['descriptor']
            mass = []
            for i in range(512):
                mass.append(descriptor[str(i)])
            current_frame_face_feature_list.append(mass)
            
            for k in range(1):
                current_frame_face_name_list.append("unknown")
                current_frame_face_name_list2.append("unknown")
                current_frame_e_distance_list = []
                current_frame_e_distance_list2 = []
                for i in range(len(face_feature_known_list)):
                    if len(face_feature_known_list[i]) > 0:
                        if str(face_feature_known_list[i][0]) != '0.0':
                            e_distance_tmp = cosine(face_feature_known_list[i][0], current_frame_face_feature_list[k])
                            e_distance_tmp2 = return_euclidean_distance(face_feature_known_list[i][0], current_frame_face_feature_list[k])
                            current_frame_e_distance_list.append(e_distance_tmp)
                            current_frame_e_distance_list2.append(e_distance_tmp2)
                        else:
                            current_frame_e_distance_list.append(999999999)
                            current_frame_e_distance_list2.append(999999999)
                    else:
                        current_frame_e_distance_list.append(999999999)
                        current_frame_e_distance_list2.append(999999999)

                similar_person_num = current_frame_e_distance_list.index(min(current_frame_e_distance_list))
                similar_person_num2 = current_frame_e_distance_list2.index(min(current_frame_e_distance_list2))

                if min(current_frame_e_distance_list) <= 0.28:
                    current_frame_face_name_list[k] = face_name_known_list[similar_person_num]

                if min(current_frame_e_distance_list2) <= 2.0:
                    current_frame_face_name_list2[k] = face_name_known_list[similar_person_num2]

                cosineCheck = 0
                if len(current_frame_face_name_list) >= 1:
                    for i in current_frame_face_name_list:
                        if i == 'unknown':
                            continue
                        else:
                            cosineCheck = 1
                            dataphoto = str(datetime.datetime.today())
                            dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
                            path = 'FilesArchiv/Recogn/' + id_org + '_' + id_group + '_' + i + '_' + str(username) + '_' + dataphoto +'.jpg'
                            try:
                                with open(basepath + path, 'wb+') as destination:
                                    destination.write(image_data)
                            except:
                                print('error save picture to server')
                            
                            visit = Visits()
                            visit.id_org      = id_org
                            visit.id_group    = id_group
                            visit.iin         = i
                            visit.status      = 2
                            visit.datestatus  = datetime.date.today()
                            visit.timestatus  = datetime.datetime.now()
                            visit.username    = username
                            visit.image_url   = path
                            visit.comments    = str(min(current_frame_e_distance_list))
                            visit.edited      = False
                            visit.save() 

                if cosineCheck == 0 and len(current_frame_face_name_list2) >= 1:
                    for i in current_frame_face_name_list2:
                        if i == 'unknown':
                            continue
                        else:
                            cosineCheck = 1
                            dataphoto = str(datetime.datetime.today())
                            dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
                            path = 'FilesArchiv/Recogn/' + id_org + '_' + id_group + '_' + i + '_' + str(username) + '_' + dataphoto +'.jpg'
                            try:
                                with open(basepath + path, 'wb+') as destination:
                                    destination.write(image_data)
                            except:
                                print('error save picture to server')
                            
                            visit = Visits()
                            visit.id_org      = id_org
                            visit.id_group    = id_group
                            visit.iin         = i
                            visit.status      = 2
                            visit.datestatus  = datetime.date.today()
                            visit.timestatus  = datetime.datetime.now()
                            visit.username    = username
                            visit.image_url   = path
                            visit.comments    = str(min(current_frame_e_distance_list2))
                            visit.edited      = False
                            visit.save() 

                # if cosineCheck == 1:
                #     asd = 1
                #     try:
                #         payload = {
                #                     'image_name': id_org + '_' + id_group + '_' + i + '_' + str(username) + '_' + dataphoto +'.jpg',
                #                     'id_org': id_org,
                #                     'id_group': id_group,
                #                     'iin': i,
                #                     'username': str(username),
                #                     'tip': 'recogn'
                #                 }       
                #         requests.post('http://192.168.5.15/filter_fake', json = payload, timeout = 2)                                           
                #     except:
                #         a = 1
                # else:                 
                #     dataphoto = str(datetime.datetime.today())
                    # dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
                    # path = 'FilesArchiv/Unrecogn/' + id_org + '_' + id_group + '_' + str(username) + '_' + dataphoto +'.jpg'
                    # try:
                    #     with open(basepath + path, 'wb+') as destination:
                    #         destination.write(image_data)
    
                    #     with open('C:/myback_dev/logs/mobile_view.log', 'a') as f:
                    #         f.write('--------------------------------------------------\n')
                    #         f.write('BIN: ' + id_org + '  ID_group: ' + id_group + '\n')
                    #         f.write('cosinus: '+ str(current_frame_e_distance_list) + '\n')
                    #         f.write('euclide:' + str(current_frame_e_distance_list2) + '\n')
                    #         f.write('cos min: '+ str(min(current_frame_e_distance_list)) + '   eucl min: '+ str(min(current_frame_e_distance_list2)) +'\n')
                    #         f.write('path:' + path + '\n')
                    #         f.write('--------------------------------------------------\n')
                    # except:
                    #     print('error save picture to server')

    result = statusfromDB(id_org, id_group, filterstatus)
    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['POST'])
def register1024(request):
    global i
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)
    
    return HttpResponse('{"status": "Обновите приложение из Play market. У Вас устаревшая версия Taimas!"}', content_type="application/json", status = 400) 

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    child_id = request.GET.get("iin")
    filterstatus = request.GET.get("filterstatus")
    datastr = request.body
    res = json.loads(datastr)
    facedata = res['facedata']
    mass_image = res['image']


    query = f"""with chlds as (SELECT iin, max(name) as nameface From serviceback_childs 
                                WHERE id_org = '{id_org}' and registered and not is_delete
			   					group by iin)
                select descrs.id_face1024, descrs.iin, chlds.nameface from serviceback_descriptors as descrs
                left join chlds on
                    chlds.iin=descrs.iin
                where descrs.iin in (select iin from chlds) and not descrs.id_face1024 = ''"""
        
    with connection.cursor() as cursor:
        cursor.execute(query, [id_org, id_group])
        result = cursor.fetchall()

    curDescruptions = facedata['description']
    is_found = False
    for row in result:
        baseDescription = eval(row[0])
        for curOneDesc in curDescruptions:
            if len(curOneDesc) == len(baseDescription):
                dist = similarity(curOneDesc,baseDescription)
                # print(row[2])
                if dist >=0.9:
                    return HttpResponse('{"status": "Данное лицо уже зарегистрировано. ' + str(row[2]) + ' "}', content_type="application/json", status = 400) 
            else:
                return HttpResponse('{"status": "Обновите приложение. Сделайте перерегистрацию лица."}', content_type="application/json", status = 400) 



    descs = Descriptors.objects.filter(iin = child_id)
    for desc in descs:
        desc.delete()

    dataphoto = str(datetime.datetime.today())
    dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')


    for i in range(1, 4):
        path = 'FilesArchiv/Register/' + id_org + '_' + id_group + '_' + child_id + '_'+ dataphoto + str(i) + '.jpg'
        with open(basepath + path, 'wb+') as destination:
            imageelem = base64.b64decode(mass_image[i-1][0])
            destination.write(imageelem)
        

        newdesc = Descriptors()
        newdesc.iin = child_id
        newdesc.id_face1024 = facedata['description'][i-1]
        newdesc.image_url = path
        newdesc.create_date = datetime.datetime.now()
        newdesc.save()

    try:
        im = Image.open(basepath + path)
        boxx = facedata['box'][0]
        im_crop = im.crop((boxx[1], boxx[0], boxx[1]+boxx[3], boxx[2]+boxx[0]))
        pathface = 'FilesArchiv/Icons/'+ child_id + '_' + dataphoto + '.jpg'
        im_crop.save(basepath + pathface, quality=5)
    except:
        im = 1

    

    childobj = Childs.objects.filter(id_org = id_org, id_group = id_group, iin = child_id, is_delete = False)
    for item in childobj:
        item.registered = True
        item.image_url  = path
        # item.icon_url   = pathface
        item.save()

    result = statusfromDB(id_org, id_group, filterstatus)
    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['POST'])
def sendphotochild(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)
    
    
    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    filterstatus = request.GET.get("filterstatus")
    datastr = request.body
    res = json.loads(datastr) 
    iin = res['iin']
    facedata = res['facedata']

    resvis = Visits.objects.filter(id_group = id_group, id_org = id_org, iin = iin, datestatus = datetime.date.today(),status = '10')
    if resvis.count() > 0:
        return HttpResponse('{"status": "Фото ребенка уже определен как ложный"}', content_type="application/json", status = 400)

    
    strb64 = facedata['canvas']
    image_data = base64.b64decode(strb64)

    dataphoto = str(datetime.datetime.today())
    dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
    path = 'FilesArchiv/Recogn/' + id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg'
    with open(basepath + path, 'wb+') as destination:
        destination.write(image_data)


    try:
        with transaction.atomic():
            box = facedata['box']
            payload = {'image_name': id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg',
                        'box': box}       
            resp = requests.post('http://192.168.5.29:8585/filter_fake', json = payload, timeout = 2000) 
            respjson = json.loads(resp.content)

            try:
                coords = res['coordinates']['coords']
            except:
                coords = None


            confidence_fake = respjson['confid']
            if confidence_fake <= 0.8:
                newfake = FakeCountByIIN()
                newfake.iin = iin
                newfake.create_date = datetime.datetime.now()
                newfake.confidence = confidence_fake
                try:
                    newfake.count = facedata['comments'] * 1000
                except:
                    newfake.count = 0
                newfake.save()

                fakescount = FakeCountByIIN.objects.filter(iin=iin, create_date = datetime.datetime.now()).count()
                if fakescount >= 3:
                    visit = Visits()
                    visit.id_org = id_org
                    visit.id_group = id_group
                    visit.iin = iin
                    visit.status = '10'
                    visit.datestatus = datetime.date.today()
                    visit.timestatus = datetime.datetime.now()
                    visit.username = username
                    visit.image_url = path
                    visit.srvcolumn = coords
                    visit.edited = False
                    visit.fakeresult = confidence_fake
                    visit.save()

                    result = statusfromDB(id_org, id_group, filterstatus)
                    return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    return HttpResponse('{"status": "Попробуйте еще раз. Осталось ' + str(3-fakescount) + ' попыток"}', content_type="application/json", status = 400)
            else:
                id_Descriptors = 0
                id_visit = 0

                visit = Visits()
                visit.id_org = id_org
                visit.id_group = id_group
                visit.iin = iin
                visit.status = '2'
                visit.datestatus = datetime.date.today()
                visit.timestatus = datetime.datetime.now()
                visit.username = username
                visit.image_url = path
                visit.comments = 'new128_' + str(facedata['comments'])
                visit.edited = False
                visit.srvcolumn = coords
                visit.fakeresult = respjson['confid']
                visit.save()

                id_visit = visit.id

                newdesc = Descriptors()
                newdesc.iin = iin
                newdesc.id_face128 = facedata['descriptor']
                newdesc.image_url = path
                newdesc.create_date = datetime.datetime.now()
                newdesc.save()

                id_Descriptors = newdesc.id

                try:
                    request_thread = threading.Thread(target=send_async_request_childphoto, args=(iin,id_Descriptors,id_visit,path,id_org,id_group,username.username))
                    request_thread.start()
                except:
                    a = 1

                try:
                    chats = TelegramData.objects.get(iin=iin)
                    token = '6677571095:AAFEpbRyIAPXHvVg6sLttUYPZeOryYqvAe8'
                    bot = telebot.TeleBot(token)
                    chatId = chats.chatid
                    send= 'Вас ребенок успешно прошел отметку посещения в детском садике '+str(iin) + ' в ' + str(datetime.date.today())
                    bot.send_message(chatId, send)
                except:
                    a = 1

                descs = Descriptors.objects.filter(iin=iin).order_by('id')
                count = descs.count()
                if count > 15:
                    for i in range(count - 15):
                        descs[i].delete()

                result = statusfromDB(id_org, id_group, filterstatus)
                return HttpResponse(json.dumps(result), content_type="application/json")

    except Exception as e:
        return HttpResponse('{"status": "Ошибка данных. Попробуйте еще раз"}', content_type="application/json", status = 400)


    
def send_async_request_childphoto(iin,id_Descriptors,id_visit,path,id_org,id_group,username):
    url = 'http://192.168.5.22:3000/detectface'  # Замените URL на целевой
    
    try:
        
        data ={
        'id_Descriptors': id_Descriptors,
        'id_visit': id_visit,
        'iin': iin,
        'path': path,
        'org': id_org,
        'group': id_group,
        'username': username
        }

        response = requests.post(url, json=data)
        response.raise_for_status()  # Проверка на ошибки при запросе
        # Обработка ответа, если это необходимо
    except Exception as e:
        print(f'Ошибка при отправке запроса: {str(e)}')




@api_view(['POST'])
def sendphotochildRESR(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)
    
    
    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    filterstatus = request.GET.get("filterstatus")
    datastr = request.body
    res = json.loads(datastr) 
    iin = res['iin']
    facedata = res['facedata']

    resvis = Visits.objects.filter(id_group = id_group, id_org = id_org, iin = iin, datestatus = datetime.date.today(),status = '10')
    if resvis.count() > 0:
        return HttpResponse('{"status": "Фото ребенка уже определен как ложный"}', content_type="application/json", status = 400)

    
    strb64 = facedata['canvas']
    image_data = base64.b64decode(strb64)

    dataphoto = str(datetime.datetime.today())
    dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
    path = 'FilesArchiv/Recogn/' + id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg'
    with open(basepath + path, 'wb+') as destination:
        destination.write(image_data)


    try:
        with transaction.atomic():
            visit = Visits()
            visit.id_org = id_org
            visit.id_group = id_group
            visit.iin = iin
            visit.status = '2'
            visit.datestatus = datetime.date.today()
            visit.timestatus = datetime.datetime.now()
            visit.username = username
            visit.image_url = path
            visit.comments = 'new128_' + str(facedata['comments'])
            visit.edited = False
            visit.save()
     

            newdesc = Descriptors()
            newdesc.iin = iin
            newdesc.id_face128 = facedata['descriptor']
            newdesc.image_url = path
            newdesc.create_date = datetime.datetime.now()
            newdesc.save()

            descs = Descriptors.objects.filter(iin=iin).order_by('id')
            count = descs.count()
            if count > 10:
                for i in range(count - 10):
                    descs[i].delete()

    except Exception as e:
        print("Ошибка при сохранении: ", e)


    try:
        box = facedata['box']
        payload = {
                    'image_name': id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg',
                    'id_org': id_org,
                    'id_group': id_group,
                    'iin': iin,
                    'username': str(username),
                    'box': box,
                    'tip': 'recogn'
                    }       
        requests.post('http://192.168.5.29:8080/filter_fake', json = payload, timeout = 0.1)                                 
    except:
        a = 1
 

    result = statusfromDB(id_org, id_group, filterstatus)
    return HttpResponse(json.dumps(result), content_type="application/json")



@api_view(['POST','GET'])
def authuser1024(request):
    
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)   
    
    username = request.user
    id_org = get_org_id(username)

    # version = request.GET.get("version")
    # if not version == "1.1":
    #     return HttpResponse('{"status": "Обновите приложение."}', content_type="application/json", status = 400) 

    query = f"""SELECT 
                    users.username, 
                    users.first_name, 
                    users.last_name,
                    profile.id_org,
                    orgs.org_name,
                    orgs.latitude,
                    orgs.longitude,
                    '00:00:01' as worktimestart,
                    '20:00:00' as worktimestop,
                    0.5 as distGPS,
                    0 as checkFake,
                    60 as camquality,
                    1920 as camheight,
                    1080 as camwidth,
                    false as errortime, 
                    orgs.checkedgps
                FROM auth_user as users
                LEFT JOIN serviceback_profileuser AS profile ON 
                    profile.name = users.username
                LEFT JOIN serviceback_organizations AS orgs ON 
                    orgs.id_org = profile.id_org
                WHERE 
                    users.username = '{username}' and not profile.is_delete"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
               for row in cursor.fetchall()]


    # myConfig = {
    #             'modelBasePath': '../../assets/facerecogn/models',
    #             'body': { 'enabled': False },
    #             'hand': { 'enabled': False },
    #             'object': { 'enabled': False },
    #             'gesture': { 'enabled': False },
    #             'filter': { 'enabled': True, 'equalization': True, 'autoBrightness': True, 'saturation': -1},
    #             'face': { 
    #                 'enabled': True,
    #                 'liveness':{'enabled': False},
    #                 'detector': { 'enabled': True, 'minConfidence': 0.3,'rotation': True},
    #                 'description': { 'enabled': True},
    #                 'emotion': { 'enabled': False},
    #                 'iris': { 'enabled': False},
    #                 'mesh': { 'enabled': False}  
    #                 }
    #             }

    respon = {
        'result': result,
        # 'humanjs': myConfig
    }

    return HttpResponse(json.dumps(respon, cls=DjangoJSONEncoder), content_type="application/json")


@api_view(['POST'])
def register128(request):
    global i
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    child_id = request.GET.get("iin")
    filterstatus = request.GET.get("filterstatus")
    datastr = request.body
    res = json.loads(datastr)
    facedata = res['facedata']
    mass_image = res['image']


    query = f"""with chlds as (SELECT iin, max(name) as nameface From serviceback_childs 
                                WHERE id_org = '{id_org}' and registered and not is_delete
			   					group by iin)
                select descrs.id_face128, descrs.iin, chlds.nameface from serviceback_descriptors as descrs
                left join chlds on
                    chlds.iin=descrs.iin
                where descrs.iin in (select iin from chlds) and not descrs.id_face128 = ''"""
        
    with connection.cursor() as cursor:
        cursor.execute(query, [id_org, id_group])
        result = cursor.fetchall()

    curDescruptions = facedata['description']
    is_found = False
    for row in result:
        baseDescription = list(eval(row[0]).values())
        for curOneDesc in curDescruptions:
            mass_desc = list(curOneDesc.values())
            if len(mass_desc) == len(baseDescription):
                dist = return_euclidean_distance(mass_desc,baseDescription)
                if dist < 0.29:
                    return HttpResponse('{"status": "Данное лицо уже зарегистрировано. ' + str(row[2]) + ' "}', content_type="application/json", status = 400) 
            else:
                return HttpResponse('{"status": "Обновите приложение. Сделайте перерегистрацию лица."}', content_type="application/json", status = 400) 



    descs = Descriptors.objects.filter(iin = child_id)
    for desc in descs:
        desc.delete()

    dataphoto = str(datetime.datetime.today())
    dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')

    countimg = 0
    for itemel in mass_image:
        
        path = 'FilesArchiv/Register/' + id_org + '_' + id_group + '_' + child_id + '_'+ dataphoto + str(countimg) + '.jpg'
        with open(basepath + path, 'wb+') as destination:
            imageelem = base64.b64decode(itemel)
            destination.write(imageelem)

    # for i in range(1, 4):
    #     path = 'FilesArchiv/Register/' + id_org + '_' + id_group + '_' + child_id + '_'+ dataphoto + str(i) + '.jpg'
    #     with open(basepath + path, 'wb+') as destination:
    #         imageelem = base64.b64decode(mass_image[i-1])
    #         destination.write(imageelem)
        
        newdesc = Descriptors()
        newdesc.iin = child_id
        newdesc.id_face128 = curDescruptions[countimg]
        newdesc.image_url = path
        newdesc.create_date = datetime.datetime.now()
        newdesc.save()
        countimg = countimg + 1

    
    im = Image.open(basepath + path)
    box = res['facedata']['box'][0]
    im_crop = im.crop((box['_x'], box['_y'], box['_x'] + box['_width'], box['_y'] + box['_height']))
    pathface = 'FilesArchiv/Icons/' + child_id + '_' + dataphoto + '.jpg'
    im_crop.save(basepath + pathface, quality=5)
  

    childobj = Childs.objects.filter(id_org = id_org, id_group = id_group, iin = child_id, is_delete = False)
    for item in childobj:
        item.registered = True
        item.image_url  = path
        item.icon_url   = pathface
        item.save()

    result = statusfromDB(id_org, id_group, filterstatus)
    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['POST'])
def sendphoto128(request):

    return HttpResponse('{"status": "Приложение не доступно. Актуальная версия на face.qazna24.kz"}', content_type="application/json", status = 400)

    try:
        hostname = request.META['HTTP_HOST']
    except:
        hostname = ''

    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)
    try:
        username = request.user
        id_org = get_org_id(username)
        id_group = request.GET.get("id_group")
        filterstatus = request.GET.get("filterstatus")
        datastr = request.body
        res = json.loads(datastr) 
        iin = res['iin']
        facedata = res['facedata']
    except:
        return HttpResponse('{"status": "Ошибка данных."}', content_type="application/json", status = 400)

    try:
        image_data = base64.b64decode(res['image'])
    except:
        image_data = ''

    query = f"""with vsts as (select iin from serviceback_visits
			                where status = '10' and datestatus = '{datetime.date.today()}' and id_org = '{id_org}' and id_group = '{id_group}' and iin = '{iin}') 
                     select id_face128, iin, id from serviceback_descriptors
                            where iin = '{iin}' and not iin in (select * from vsts) and not id_face128 = ''
                            order by id
                            """
        
    with connection.cursor() as cursor:
        cursor.execute(query, [id_org, id_group])
        result = cursor.fetchall()



    curDescruption = list(facedata['description'].values())
    is_found = False

    mass_dist = []
    for row in result:
        baseDescription = list(eval(row[0]).values()) 
        if len(curDescruption) == len(baseDescription):
            dist = return_euclidean_distance(curDescruption,baseDescription)
            mass_dist.append(dist)
    # if len(mass_dist)>0:
    #     if min(mass_dist) <= 0.05:
    #         return HttpResponse('{"status": "Некорректое фото. Повторите попытку."}', content_type="application/json", status = 400) 



    for row in result:
        baseDescription = list(eval(row[0]).values()) 
        if len(curDescruption) == len(baseDescription):
            dist = return_euclidean_distance(curDescruption,baseDescription)
            if dist <= 0.35:
                dataphoto = str(datetime.datetime.today())
                dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
                path = 'FilesArchiv/Recogn/' + id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg'
                try:
                    with open(basepath + path, 'wb+') as destination:
                        destination.write(image_data)
                except:
                    a = 1


                visit = Visits()
                visit.id_org = id_org
                visit.id_group = id_group
                visit.iin = iin
                visit.status = 2
                visit.datestatus = datetime.date.today()
                visit.timestatus = datetime.datetime.now()
                visit.username = username
                visit.image_url = path
                visit.comments = 'd128_' + str(min(mass_dist))
                visit.edited = False
                # visit.hostname = hostname
                visit.save()

                try:
                    box = res['facedata']['box']
                    payload = {
                                    'image_name': id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg',
                                    'id_org': id_org,
                                    'id_group': id_group,
                                    'iin': iin,
                                    'username': str(username),
                                    'box': box,
                                    'tip': 'recogn'
                                }       
                    requests.post('http://192.168.5.29:8080/filter_fake', json = payload, timeout = 0.1)                                      
                except:
                    a = 1


                newdesc = Descriptors()
                newdesc.iin = iin
                newdesc.id_face128 = str(facedata['description'])
                newdesc.image_url = path
                newdesc.create_date = datetime.datetime.now()
                newdesc.save()


                countdesc = len(result)+1
                if countdesc>10:
                    razn = countdesc - 10
                    for cnt in range(razn):
                        id_desc = result[cnt][2]
                        try:
                            records_to_delete = Descriptors.objects.get(pk = id_desc)
                            records_to_delete.delete()
                        except:
                            a =1



                # resdescs = Descriptors.objects.filter(iin = iin).order_by('id')

                # Descriptors.objects.delete(id = )
                # countdesc = resdescs.count()
                # if countdesc > 10:
                #     raznica = countdesc - 10
                #     for itemdesc in resdescs:
                #         itemdesc.delete()
                #         raznica = raznica - 1
                #         if raznica == 0:
                #             break
                is_found = True
                break
        else:
            return HttpResponse('{"status": "Обновите приложение. Сделайте перерегистрацию лица."}', content_type="application/json", status = 400) 
    
    if is_found==False and len(result) > 250:
        dataphoto = str(datetime.datetime.today())
        dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
        path2 = 'FilesArchiv/Recogn/' + id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg'
        with open(basepath + path2, 'wb+') as destination:
            destination.write(image_data)

        newdesc = Descriptors()
        newdesc.iin = iin
        newdesc.id_face128 = str(facedata['description'])
        newdesc.image_url = path2
        newdesc.create_date = datetime.datetime.now()
        newdesc.save()  


        visit = Visits()
        visit.id_org = id_org
        visit.id_group = id_group
        visit.iin = iin
        visit.status = 2
        visit.datestatus = datetime.date.today()
        visit.timestatus = datetime.datetime.now()
        visit.username = username
        visit.image_url = path2
        visit.comments = 'd128_insertdesc'
        # visit.hostname = hostname
        visit.edited = False
        visit.save()
        is_found = True


        try:
            box = res['facedata']['box']
            payload = {
                                    'image_name': id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg',
                                    'id_org': id_org,
                                    'id_group': id_group,
                                    'iin': iin,
                                    'username': str(username),
                                    'box': box,
                                    'tip': 'recogn'
                                }       
            requests.post('http://192.168.5.29:8080/filter_fake', json = payload, timeout = 0.1)                                      
        except:
            a = 1

    # max_dist = 0.4
    # if is_found==False and len(mass_dist)>0:
    #     max_dist = max(mass_dist)
    #     if max_dist <=0.35:
    #         dataphoto = str(datetime.datetime.today())
    #         dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
    #         path = 'FilesArchiv/Recogn/' + id_org + '_' + id_group + '_' + iin + '_' + str(username) + '_' + dataphoto +'.jpg'
    #         with open(basepath + path, 'wb+') as destination:
    #             destination.write(image_data)

    #         newdesc = Descriptors()
    #         newdesc.iin = iin
    #         newdesc.id_face128 = str(facedata['description'])
    #         newdesc.image_url = path
    #         newdesc.create_date = datetime.datetime.now()
    #         newdesc.save()  


            # visit = Visits()
            # visit.id_org = id_org
            # visit.id_group = id_group
            # visit.iin = iin
            # visit.status = 2
            # visit.datestatus = datetime.date.today()
            # visit.timestatus = datetime.datetime.now()
            # visit.username = username
            # visit.image_url = path2
            # visit.comments = str(max_dist)
            # visit.edited = False
            # visit.save()
            # is_found = True


    if is_found:
        result = statusfromDB(id_org, id_group, filterstatus)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else: 
        # dataphoto = str(datetime.datetime.today())
        # dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
        # mindist = '0.9999'
        # if len(mass_dist)>0:
        #     mindist = str(min(mass_dist))
        # path = 'FilesArchiv/Unrecogn/' + id_org + '_' + id_group + '_' + iin + '_' + dataphoto + '_' + mindist +'.jpg'
        # try:
        #     with open(basepath + path, 'wb+') as destination:
        #         destination.write(image_data)
        # except:
        #     asd = 1
        return HttpResponse('{"status": "Лицо не разпознано. Повторите еще раз!"}', content_type="application/json", status = 400) 


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getFakeImgUrl(request):
    query = f"""WITH	visit as (select * from serviceback_visits
                  where datestatus = '21-05-2023'),
        tmptbl as (select iin, max(timestatus) as timestatus from visit
                   group by iin),
        resvisit as (select * from visit
                     where (iin, timestatus) in (select iin, timestatus from tmptbl) and status = '10'),
		orgs as (select * from serviceback_organizations
				where id_org in (select id_org from resvisit)),
		allgrps as (select * from serviceback_groups
				where (id_org, id_group) in (select id_org, id_group from resvisit) and not is_delete),
		allchlds as (select * from serviceback_childs
				where (id_org, id_group, iin) in (select id_org, id_group, iin from resvisit) and not is_delete)
		
        select  resvisit.id, resvisit.iin, allchlds.name as childname, 
                replace(resvisit.image_url, 'FilesArchiv', 'https://face11.qazna24.kz/media') as image_url,
                orgs.bin, orgs.org_name, allgrps.group_name from resvisit
        left join orgs on
            resvisit.id_org = orgs.id_org
        left join allgrps on
            resvisit.id_org = allgrps.id_org and resvisit.id_group = allgrps.id_group
        left join allchlds on
            resvisit.id_org = allchlds.id_org and resvisit.id_group = allchlds.id_group and resvisit.iin = allchlds.iin
        limit 1"""

    with connection.cursor() as cursorgr:
        cursorgr.execute(query)
        columnsgr = [col[0] for col in cursorgr.description]
        resultgr = [dict(zip(columnsgr, rowgr))
               for rowgr in cursorgr.fetchall()]

    return HttpResponse(json.dumps(resultgr), content_type="application/json")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def changestatusbyadm(request):
    username = request.user
    case = request.GET.get("case")
    id_zap = request.GET.get("id")
    if case == 'real':
        try:
            objvisit = Visits.objects.get(id = id_zap)
            objvisit.status = '2'
            objvisit.comments = 'проверен ' + str(username)
            objvisit.save()
        except:
            a = 1
    if case == 'fake':
        objvisit = Visits.objects.get(id = id_zap)
        objvisit.comments = 'проверен ' + str(username)
        # objvisit.username = str(username)  
        objvisit.save()
    
    query = f"""WITH resvisit as (
                        select 
                            * 
                        from 
                            serviceback_visits
                        where 
                            status='10'
                            and datestatus = '{datetime.date.today()}'
                            and comments is null),
		            orgs as (
                        select 
                            id_org,
                            org_name 
                        from 
                            serviceback_organizations
				        where 
                            id_org in (
                                select 
                                    id_org 
                                from 
                                    resvisit)),
                    tempusers as(
                        SELECT
                            username,
                            first_name
                        FROM
                            auth_user
                        WHERE
                            username in (
                                    SELECT
                                        username
                                    FROM
                                        resvisit)),
		            allgrps as (
                        select 
                            id_org,
                            id_group,
                            group_name 
                        from 
                            serviceback_groups
				        where (id_org, id_group) in (
                                    select 
                                        id_org, 
                                        id_group 
                                    from 
                                        resvisit) 
                                and not is_delete),
		            allchlds as (
                            select 
                                * 
                            from 
                                serviceback_childs
				            where iin in (
                                    select 
                                        iin 
                                    from 
                                        resvisit)
                                    and not is_delete)		
                    select  
                        resvisit.id, 
                        resvisit.iin, 
                        allchlds.name as childname, 
                        replace(resvisit.image_url, 'FilesArchiv', 'https://face11.qazna24.kz/media') as image_url,
                        resvisit.id_org, 
                        orgs.org_name, 
                        allgrps.group_name,
                        us.first_name as username
                    from 
                        resvisit
                    left join
                        orgs 
                    on
                        resvisit.id_org = orgs.id_org
                    left join 
                        allgrps 
                    on
                        resvisit.id_org = allgrps.id_org 
                        and resvisit.id_group = allgrps.id_group
                    left join 
                        allchlds 
                    on
                        resvisit.iin = allchlds.iin
                    left join 
                        tempusers as us 
                    on
                        resvisit.username = us.username
                    limit 1"""

    with connection.cursor() as cursorgr:
        cursorgr.execute(query)
        columnsgr = [col[0] for col in cursorgr.description]
        resultgr = [dict(zip(columnsgr, rowgr))
               for rowgr in cursorgr.fetchall()]

    return HttpResponse(json.dumps(resultgr), content_type="application/json")




def normalize_distance(dist: float, order: int, min_: float, max_: float) -> float:
    if dist == 0:
        return 1
    root = math.sqrt(dist) if order == 2 else dist ** (1 / order)
    norm = (1 - (root / 100) - min_) / (max_ - min_)
    clamp = max(min(norm, 1), 0)
    return clamp



def distance(descriptor1: List[float], descriptor2: List[float], options: Dict[str, Any] = {'order': 2, 'multiplier': 25}) -> float:
    if not descriptor1 or not descriptor2:
        return float('inf')
    sum_ = 0
    for i in range(len(descriptor1)):
        diff = (descriptor1[i] - descriptor2[i]) if not options['order'] or options['order'] == 2 else abs(descriptor1[i] - descriptor2[i])
        sum_ += (diff * diff) if not options['order'] or options['order'] == 2 else (diff ** options['order'])
    return (options['multiplier'] or 20) * sum_



def similarity(descriptor1: List[float], descriptor2: List[float], options: Dict[str, Any] = {'order': 2, 'multiplier': 25, 'min': 0.2, 'max': 0.8}) -> float:
    dist = distance(descriptor1, descriptor2, options)
    return normalize_distance(dist, options.get('order', 2), options.get('min', 0.2), options.get('max', 0.8))