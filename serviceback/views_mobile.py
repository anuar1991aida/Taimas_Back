from django.http import HttpResponse
from rest_framework.decorators import api_view
import os, datetime, base64, json, requests
from time import time
from django.utils import timezone
from PIL import Image #pip install Pillow
from urllib3.exceptions import InsecureRequestWarning #added
from .models import Childs, Organizations, Groups, Visits, ProfileUser
from django.db import connection
import numpy as np


# *******************************************
# Системные функции для работы приложения
# *******************************************
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
basepath = '//192.168.5.22'
def get_org_id(username):
    usrobj = ProfileUser.objects.all()
    usrobj = usrobj.filter(name = username)
    for itemorg in usrobj:
        id_org = itemorg.id_org
    return id_org

def statusfromDB(id_org, id_group):
    query = f"""
                WITH
                    visit as (select * from serviceback_visits				  
                    where id_org = '{id_org}' and id_group = '{id_group}' and datestatus = '{datetime.date.today()}'),
                    tmptbl as (select iin, max(timestatus) as timestatus from visit
                    group by iin),
                    resvisit as (
                    select visit.* from visit
                        join tmptbl on
                        visit.iin = tmptbl.iin and
                        visit.timestatus = tmptbl.timestatus
                    )
                SELECT 
                    childs.iin, 
                    childs.name,
                    CASE
                        WHEN NOT childs.registered  THEN '0'
                        WHEN visits.status IS NULL  THEN '1'
                        ELSE visits.status
                    END as status,
                    CASE
                        WHEN NOT childs.registered  THEN 'Первичная идентификация'
                        WHEN visits.status IS NULL  THEN 'Ожидают сканирования'
                        WHEN visits.status = '2'    THEN to_char(visits.create_date::timestamp, 'DD-MM-YYYY HH24:MI:SS')
                        WHEN visits.status = '3'    THEN 'Больничный'
                        WHEN visits.status = '4'    THEN 'Отпуск'
                        WHEN visits.status = '10'   THEN 'Ложное фото. Действие зафиксировано!'
                        ELSE 'Статус не определен'
                    END as statusname 
                FROM serviceback_childs as childs
                LEFT JOIN resvisit as visits ON
                    visits.id_org = childs.id_org
                    and visits.id_group = childs.id_group
                    and visits.iin = childs.iin
                    and visits.datestatus = '{datetime.date.today()}'
                WHERE 
                    childs.id_org = '{id_org}' and childs.id_group = '{id_group}'
                ORDER BY childs.name
                """

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
               for row in cursor.fetchall()]
    return result


@api_view(['POST','GET'])
def setstatus(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)
    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    iin = request.GET.get("iin")
    status = request.GET.get("status")
    itemGr = Visits(id_group = id_group, id_org = id_org, iin = iin, status = status, datestatus = datetime.datetime.today(), timestatus = datetime.datetime.now(), create_date = datetime.datetime.now())
    itemGr.save()
    result = statusfromDB(id_org, id_group)
    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['POST','GET'])
def authuser(request):
    
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)   
    
    username = request.user
    # id_org = get_org_id(username)

    query = """SELECT 
                    users.username, 
                    users.first_name, 
                    users.last_name,
                    profile.id_org,
                    orgs.org_name,
                    orgs.latitude,
                    orgs.longitude,
                    orgs.checkedgps
                FROM auth_user as users
                LEFT JOIN serviceback_profileuser AS profile ON 
                    profile.name = users.username
                LEFT JOIN serviceback_organizations AS orgs ON 
                    orgs.id_org = profile.id_org
                WHERE 
                    users.username = %s"""

    with connection.cursor() as cursor:
        cursor.execute(query, [str(username)])
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
               for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result), content_type="application/json")


@api_view(['GET'])
def groupstatus(request):
    username = request.user
    id_org = get_org_id(username)

    query = f"""WITH
                    visit as (select * from serviceback_visits				  
                                where id_org = '{id_org}' and datestatus = '{datetime.date.today()}'),
                                tmptbl as (select iin, max(create_date) as create_date from visit
                                group by iin),
                    resvisit as (
                                select visit.* from visit
                                    join tmptbl on
                                    visit.iin = tmptbl.iin and
                                    visit.create_date = tmptbl.create_date
                                ),
					statustable as (SELECT 
                                    childs.id_group,
                                    childs.iin, 
                                    childs.name,
                                    CASE
                                        WHEN NOT childs.registered  THEN '0'
                                        WHEN visits.status IS NULL  THEN '1'
                                        ELSE visits.status
                                    END as status 
                                FROM serviceback_childs as childs
                                LEFT JOIN resvisit as visits ON
                                    visits.id_org = childs.id_org
                                    and visits.id_group = childs.id_group
                                    and visits.iin = childs.iin
                                    and visits.datestatus = '{datetime.date.today()}'
                                WHERE 
                                    childs.id_org = '{id_org}' 
                                ORDER BY childs.name),
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
                                    END as notvisited,
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
                                        WHEN statustable.status in ('2','3','4')  THEN 1
                                        ELSE 0
                                    END as checked,
                                    statustable.status as common
                                FROM serviceback_groups as groupstbl
                                LEFT JOIN statustable ON 
                                        groupstbl.id_group = statustable.id_group
                                WHERE 
                                    groupstbl.id_org = '{id_org}' and groupstbl.username = '{username}')

                    select id_group, id_org, group_name, 
                            sum(notregister) as notreg, 
                            sum(notvisited) as notvis, 
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
def childstatus(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)

    id_org = get_org_id(request.user)
    id_group = request.GET.get("id_group")
    result = statusfromDB(id_org, id_group)
    return HttpResponse(json.dumps(result), content_type="application/json")

         

@api_view(['GET'])
def childphoto(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    iin = request.GET.get("iin")

    encoded_string = ""
    pathdir = '//192.168.5.17/ssd/Register/' + id_org + '/' + id_group +'/C' + iin

    direxist = os.path.isdir(pathdir)
    if direxist:
        listOfFiles = os.listdir(pathdir)
        for res in listOfFiles:
            #Получаем первый фото файл (пока что путь)
            namephoto = res
            break

        #Получаем временный файл после записи
        image = Image.open(pathdir + '/' + namephoto)

        pathsavetemp = 'C:/myback_dev/tmp/' + id_org + '_' + id_group +'_' + iin + '_quality.jpg'
        fileexist = os.path.exists(pathsavetemp)
        #Если существует файл временной папке, удаляем его
        if fileexist:
            os.remove(pathsavetemp)
        # Сохраним со сжатием
        image = image.convert('RGB')
        image.save(pathsavetemp,quality=10,optimize=True)
        with open(pathsavetemp, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())    
        resp = {'image': encoded_string.decode("utf-8")}
        os.remove(pathsavetemp) #Удаляем временный файл после чтения


    return HttpResponse(json.dumps(resp, indent=2), content_type="application/json")



@api_view(['GET'])
def childhistory(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)

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



def face_comparison(mass,id_org):
    face_name_known_list = []
    face_feature_known_list = []
    current_frame_face_feature_list = []
    current_frame_face_name_list = []

    query = """SELECT id_face,iin From serviceback_childs 
                    WHERE 
                        id_org = %s and not id_face ='';
                """



    with connection.cursor() as cursor:
        cursor.execute(query, [id_org])
        result = cursor.fetchall()
        if len(result)==0:
            return True
        for row in result:
            features_someone_arr = []
            face_name_known_list.append(row[1])
            raz = row[0].split()
            for z in raz:
                   s = z.strip()
                   features_someone_arr.append(float(s))
            face_feature_known_list.append(features_someone_arr)
    
    vremennaya = []
    for q in mass.split():
        vremennaya.append(float(q))
    current_frame_face_feature_list.append(vremennaya)

    for k in range(len(current_frame_face_feature_list)):
        current_frame_face_name_list.append("unknown")
        current_frame_e_distance_list = []
        for i in range(len(face_feature_known_list)):
            if len(face_feature_known_list[i]) > 0:
                if str(face_feature_known_list[i][0]) != '0.0':
                    e_distance_tmp = return_euclidean_distance(current_frame_face_feature_list[k],face_feature_known_list[i])
                    current_frame_e_distance_list.append(e_distance_tmp)
                else:
                    current_frame_e_distance_list.append(999999999)
            else:
                current_frame_e_distance_list.append(999999999)

        similar_person_num = current_frame_e_distance_list.index(min(current_frame_e_distance_list))
        if min(current_frame_e_distance_list) < 0.4:
            current_frame_face_name_list[k] = face_name_known_list[similar_person_num]

    if len(current_frame_face_name_list)>0:
        if current_frame_face_name_list[0] != 'unknown':
            return False
        else:
            return True    
    else:
        return True



@api_view(['POST'])
def register(request):
    global i
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)

    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    child_id = request.GET.get("iin")
    datastr = request.body
    res = json.loads(datastr)
    detects = res['detects']
    try:
        image_data = base64.b64decode(res['image'][0])
    except:
        image_data = base64.b64decode(res['image'])

    if 1 == 1:    
        mass = ""
        for i in range(128):
            mass = mass + ' ' +  str(detects['descriptor'][str(i)])

        result_face = face_comparison(mass,id_org)
        if result_face == False:
            return HttpResponse('{"status": "Лицо уже зарегистрировано в системе"}', content_type="application/json",status = 403)

        # print(id_org + "  " + id_group + "  " + child_id)
        pathdir = '//192.168.5.17/ssd/Register/' + id_org + '/' + id_group +'/C' + child_id
        pathorg = '//192.168.5.17/ssd/Register/' + id_org
        direxist = os.path.isdir(pathorg)
        if not direxist:
            os.mkdir(pathorg)
        pathgroup = '//192.168.5.17/ssd/Register/' + id_org + '/' + id_group
        direxist = os.path.isdir(pathgroup)
        if not direxist:
            os.mkdir(pathgroup)
        pathchild = '//192.168.5.17/ssd/Register/' + id_org + '/' + id_group +'/C' + child_id
        direxist = os.path.isdir(pathchild)
        if not direxist:
            os.mkdir(pathchild)
        listOfFiles1 = os.listdir(pathdir)
        for res1 in listOfFiles1:
            #print('remuved iin:' + res1)
            os.remove(pathdir + '/' + res1)    
        pathfile = pathdir + '/' + child_id + '.jpg'
        with open(pathfile, 'wb+') as destination:
            destination.write(image_data)


        childobj = Childs.objects.all()
        childobj = childobj.filter(id_org = id_org, id_group = id_group, iin = child_id)
        for item in childobj:
            item.id_face = mass
            item.registered = True
            item.save()
        result = statusfromDB(id_org, id_group)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        return HttpResponse('{"status": "На фото несколько лиц"}', content_type="application/json",status = 500)



def return_euclidean_distance(feature_1, feature_2):
        feature_1 = np.array(feature_1)
        feature_2 = np.array(feature_2)
        dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
        return dist



@api_view(['POST'])
def sendphotogroup(request):
    if request.user.is_anonymous:
        return HttpResponse('{"status": "Ошибка авторизации."}', content_type="application/json", status = 401)
    
    username = request.user
    id_org = get_org_id(username)
    id_group = request.GET.get("id_group")
    datastr = request.body
    res = json.loads(datastr)
    try:
        image_data = base64.b64decode(res['image'][0])
    except:
        image_data = base64.b64decode(res['image'])

    detects = res['detects']
    
    children_list = ''
    massiin = ""

    if 1 > 0:
        face_name_known_list = []
        face_feature_known_list = []

        query = """SELECT id_face,iin From serviceback_childs 
                    WHERE 
                        id_org = %s and id_group = %s and not id_face ='';
                """



        with connection.cursor() as cursor:
            cursor.execute(query, [id_org, id_group])
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
                            e_distance_tmp = return_euclidean_distance(current_frame_face_feature_list[k],face_feature_known_list[i])
                            current_frame_e_distance_list.append(e_distance_tmp)
                        else:
                            current_frame_e_distance_list.append(999999999)
                    else:
                        current_frame_e_distance_list.append(999999999)

                similar_person_num = current_frame_e_distance_list.index(min(current_frame_e_distance_list))
                if min(current_frame_e_distance_list) < 0.4:
                    current_frame_face_name_list[k] = face_name_known_list[similar_person_num]
            

                children_list = ''
               
                if len(current_frame_face_name_list) >= 1:
                    for i in current_frame_face_name_list:
                        if i == 'unknown':
                            continue
                        else:
                            visit = Visits()
                            visit.id_org      = id_org
                            visit.id_group    = id_group
                            visit.iin         = i
                            visit.status      = 2
                            visit.datestatus  = datetime.date.today()
                            visit.timestatus  = datetime.datetime.now()
                            visit.create_date = datetime.datetime.now()
                            visit.save() 
                            if massiin=="":
                                massiin = "'" + i + "'"
                            else:
                                massiin = massiin + ', ' +  "'" + i + "'"
                            children_list = children_list + '-' + i
  
    
    if children_list !=  '':
        dataphoto = str(datetime.datetime.today())
        dataphoto = dataphoto.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
        path = '//192.168.5.17/ssd/imges_Ras/' + id_org + '_' + id_group + '_' +'(' +children_list + ')' +'_'+ dataphoto +'.jpg'
        # path = '//192.168.5.22/FaceDastan/imges_Ras/result/aaaa.jpg'
        try:
            with open(path, 'wb+') as destination:
                destination.write(image_data)
        except:
            print('error save picture to server')

    result = statusfromDB(id_org, id_group)

    # query = f"""SELECT childs.iin, childs.name from serviceback_childs as childs
    #             WHERE childs.id_org = '{id_org}' and childs.id_group = '{id_group}'
    #             and childs.iin in ({massiin})""" 

    # with connection.cursor() as cursor:
    #     cursor.execute(query, [id_org, id_group, massiin])
    #     columns = [col[0] for col in cursor.description]
    #     result = [dict(zip(columns, row))
    #            for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result), content_type="application/json")


