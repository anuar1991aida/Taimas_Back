import base64, datetime, json, requests
import calendar
from urllib import request
from django.http import HttpResponse
from rest_framework.decorators import api_view
from urllib3.exceptions import InsecureRequestWarning  # added
from .models import *
from django.db import connection
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes



# *******************************************
# Системные функции для работы приложения
# *******************************************
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
basepath = '//192.168.5.29/ssd/'


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def geterrorgroup(request):
	query = f"""with chlds as (SELECT iin, id_org, id_group,image_url FROM public.serviceback_childs where registered and id_org<>'' and image_url<>''),
					desciin as (select iin from public.serviceback_descriptors where not id_face128='' group by iin),
					orgs as (select * from public.serviceback_organizations where id_org in (select id_org from chlds)),
					grps as (select * from public.serviceback_groups where (id_org, id_group) in (select id_org, id_group from chlds))
				select chlds.id_org, chlds.id_group, iin, max(replace(chlds.image_url, 'FilesArchiv/Register/', '')) as url from chlds
				where not iin in (select iin from desciin)
				group by chlds.id_org, chlds.id_group, iin"""

	with connection.cursor() as cursor:
		cursor.execute(query)
		columns = [col[0] for col in cursor.description]
		result = [dict(zip(columns, row))
            for row in cursor.fetchall()]
		return HttpResponse(json.dumps(result, default=str), content_type="application/json")

@api_view(['POST'])
def insertdesc(request):
	# id_face128 = request.GET.get("id_face128")
	child_id = request.GET.get("iin")
	datastr = request.body
	res = json.loads(datastr)
	id_face128 = res['id_face128']
	imgurl = res['url']

	newdesc = Descriptors()
	newdesc.iin = child_id
	newdesc.id_face128 = id_face128
	newdesc.image_url = imgurl
	newdesc.create_date = datetime.datetime.now()
	newdesc.save()

	return HttpResponse('{"status": "Обновите приложение. Сделайте перерегистрацию лица."}', content_type="application/json")

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def actionorgs(request):
    query = ""
    query = f"""with orgs as (select id_org, org_name from public.serviceback_organizations),
				status2 as (select id_org, count(DISTINCT iin) from public.serviceback_visits 
							where datestatus = '17-05-2023' and id_org in (select id_org from orgs) and status = '2'
							group by id_org),
				status3 as (select id_org, count(DISTINCT iin) from public.serviceback_visits 
							where datestatus = '17-05-2023' and id_org in (select id_org from orgs) and status = '3'
							group by id_org),
				status4 as (select id_org, count(DISTINCT iin) from public.serviceback_visits 
							where datestatus = '17-05-2023' and id_org in (select id_org from orgs) and status = '4'
							group by id_org),
				status10 as (select id_org, count(DISTINCT iin) from public.serviceback_visits 
							where datestatus = '17-05-2023' and id_org in (select id_org from orgs) and status = '10'
							group by id_org),
				childsall as (select id_org, count(DISTINCT iin) as cntchld from public.serviceback_childs
							where id_org in (select id_org from orgs) and not is_delete
							group by id_org),
				childsreg as (select id_org, count(iin) as regchld from public.serviceback_childs
							where id_org in (select id_org from orgs) and not is_delete and registered
							group by id_org),
				itog as (select orgs.id_org, orgs.org_name, 
						childsall.cntchld as allchlds,
						childsreg.regchld as regchlds,
						status2.count as st2,
						status3.count as st3,
						status4.count as st4,
						status10.count as st10
						from orgs
						left join childsall on
									orgs.id_org=childsall.id_org
						left join childsreg on
									orgs.id_org=childsreg.id_org
						left join status2 on
									orgs.id_org=status2.id_org
						left join status3 on
									orgs.id_org=status3.id_org
						left join status4 on
									orgs.id_org=status4.id_org
						left join status10 on
									orgs.id_org=status10.id_org
						
						)
			select * from itog
			where regchlds is null"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result, default=str), content_type="application/json")


# Сервис получения списка воспитательных групп
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dirs(request):
    qtype = request.GET.get("qtype")
    if qtype == None:
        return HttpResponse('{"status": "Не передан параметр для ответа."}', content_type="application/json", status=400)

    query = ""

    if qtype == "childs":
        query = f"""SELECT iin, name, id_group, id_org
                    FROM serviceback_childs
                    WHERE is_delete = False"""

    if qtype == "organizations":
        query = f"""SELECT id_org, org_name, bin, id_obl, id_region, count_place, type_org, type_city, type_ecolog 
                    FROM serviceback_organizations"""

    if qtype == "regions":
        query = f"""SELECT id as id_region, name, id_parent as id_oblast 
                    FROM serviceback_regions
                    WHERE not id_parent = 0"""

    if qtype == "oblast":
        query = f"""SELECT id as id_oblast, name 
                    FROM serviceback_regions
                    WHERE id_parent = 0"""

    if qtype == "groups":
        query = f"""SELECT id_group, group_name as name, group_count, category, group_age 
                    FROM serviceback_groups
                    WHERE not is_delete"""

    if query == "":
        return HttpResponse('{"status": "Некорректный параметр для ответа."}', content_type="application/json", status=400)

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    return HttpResponse(json.dumps(result, default=str), content_type="application/json")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def allvisits(request):
	paramdate1 = request.GET.get("datestart")
	datestart = datetime.datetime.strptime(paramdate1, '%d.%m.%Y').date()
	datemass = str(paramdate1).split('.')
	range = calendar.monthrange(int(datemass[2]), int(datemass[1]))
	datestop = datestart.replace(day=range[1])
	query = f"""with 
	 orgwithname as (select id_org, org_name, bin, id_obl, id_region, type_org  from serviceback_organizations),
	 groupbyorg as (select id_group, id_org, group_name, username from serviceback_groups
				   	where not is_delete),
	 childs as (select childs.iin, childs.name, childs.id_org, orgs.org_name, childs.id_group, groupbyorg.group_name from serviceback_childs as childs
				left join orgwithname as orgs on
					childs.id_org = orgs.id_org
			  	left join groupbyorg as groupbyorg on
					childs.id_group = groupbyorg.id_group and
					childs.id_org = groupbyorg.id_org
			   	where not childs.is_delete),
	 allvisits as (select * from serviceback_visits
			   	where not status = '9' and datestatus>='{datestart}' and datestatus<='{datestop}'),
	 statusmaxdate as (select id_org, id_group, iin, datestatus, max(timestatus) as timestatus from allvisits
					  group by id_org, id_group, iin, datestatus),
	 itogvisits as (select allvisits.* from allvisits
				   join statusmaxdate on
				   allvisits.id_org=statusmaxdate.id_org and 
				   allvisits.id_group=statusmaxdate.id_group and 
				   allvisits.datestatus=statusmaxdate.datestatus and
				   allvisits.timestatus=statusmaxdate.timestatus and
				   allvisits.iin=statusmaxdate.iin),
	visitbymonth as (select id_org as id_org1, id_group as id_group1, iin as iin1,
					 sum(case 
					  when date_part('day', datestatus) = 1 then 
						 			case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end 
						 else 0 
					 end) as day_1,
					 sum(case 
					  when date_part('day', datestatus) = 2 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end
						 else 0 
					 end) as day_2,
					 sum(case 
					  when date_part('day', datestatus) = 3 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_3,
					 sum(case 
					  when date_part('day', datestatus) = 4 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_4,
					 sum(case 
					  when date_part('day', datestatus) = 5 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_5,
					 sum(case 
					  when date_part('day', datestatus) = 6 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_6,
					 sum(case 
					  when date_part('day', datestatus) = 7 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_7,
					 sum(case 
					  when date_part('day', datestatus) = 8 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_8,
					 sum(case 
					  when date_part('day', datestatus) = 9 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_9,
					 sum(case 
					  when date_part('day', datestatus) = 10 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_10,
					 sum(case 
					  when date_part('day', datestatus) = 11 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_11,
					 sum(case 
					  when date_part('day', datestatus) = 12 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_12,
					 sum(case 
					  when date_part('day', datestatus) = 13 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_13,
					 sum(case 
					  when date_part('day', datestatus) = 14 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_14,
					 sum(case 
					  when date_part('day', datestatus) = 15 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_15,
					 sum(case 
					  when date_part('day', datestatus) = 16 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_16,
					 sum(case 
					  when date_part('day', datestatus) = 17 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_17,
					 sum(case 
					  when date_part('day', datestatus) = 18 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_18,
					 sum(case 
					  when date_part('day', datestatus) = 19 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_19,
					 sum(case 
					  when date_part('day', datestatus) = 20 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_20,
					 sum(case 
					  when date_part('day', datestatus) = 21 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_21,
					 sum(case 
					  when date_part('day', datestatus) = 22 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_22,
					 sum(case 
					  when date_part('day', datestatus) = 23 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_23,
					 sum(case 
					  when date_part('day', datestatus) = 24 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_24,
					 sum(case 
					  when date_part('day', datestatus) = 25 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_25,
					 sum(case 
					  when date_part('day', datestatus) = 26 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_26,
					 sum(case 
					  when date_part('day', datestatus) = 27 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_27,
					 sum(case 
					  when date_part('day', datestatus) = 28 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_28,
					 sum(case 
					  when date_part('day', datestatus) = 29 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_29,
					 sum(case 
					  when date_part('day', datestatus) = 30 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_30,
					 sum(case 
					  when date_part('day', datestatus) = 31 then case when edited then cast(status as integer) + 10
						 				 else cast(status as integer) end else 0 
					 end) as day_31
					 From itogvisits
					GROUP BY id_org, id_group,iin),				
		readytbl as (select childs.*, 
							case 
								when visitbymonth.day_1 isnull or visitbymonth.day_1='0' or visitbymonth.day_1='1'  or visitbymonth.day_1='10' then 5
								else visitbymonth.day_1
							end,
							case 
								when visitbymonth.day_2 isnull or visitbymonth.day_2='0' or visitbymonth.day_2='1'  or visitbymonth.day_2='10' then 5
								else visitbymonth.day_2
							end,
							case 
								when visitbymonth.day_3 isnull or visitbymonth.day_3='0' or visitbymonth.day_3='1'  or visitbymonth.day_3='10' then 5
								else visitbymonth.day_3
							end,
							case 
								when visitbymonth.day_4 isnull or visitbymonth.day_4='0' or visitbymonth.day_4='1'  or visitbymonth.day_4='10' then 5
								else visitbymonth.day_4
							end,
							case 
								when visitbymonth.day_5 isnull or visitbymonth.day_5='0' or visitbymonth.day_5='1'  or visitbymonth.day_5='10' then 5
								else visitbymonth.day_5
							end,
							case 
								when visitbymonth.day_6 isnull or visitbymonth.day_6='0' or visitbymonth.day_6='1'  or visitbymonth.day_6='10' then 5
								else visitbymonth.day_6
							end,
							case 
								when visitbymonth.day_7 isnull or visitbymonth.day_7='0' or visitbymonth.day_7='1'  or visitbymonth.day_7='10' then 5
								else visitbymonth.day_7
							end,
							case 
								when visitbymonth.day_8 isnull or visitbymonth.day_8='0' or visitbymonth.day_8='1'  or visitbymonth.day_8='10' then 5
								else visitbymonth.day_8
							end,
							case 
								when visitbymonth.day_9 isnull or visitbymonth.day_9='0' or visitbymonth.day_9='1'  or visitbymonth.day_9='10' then 5
								else visitbymonth.day_9
							end,
							case 
								when visitbymonth.day_10 isnull or visitbymonth.day_10='0' or visitbymonth.day_10='1'  or visitbymonth.day_10='10' then 5
								else visitbymonth.day_10
							end,
							case 
								when visitbymonth.day_11 isnull or visitbymonth.day_11='0' or visitbymonth.day_11='1'  or visitbymonth.day_11='10' then 5
								else visitbymonth.day_11
							end,
							case 
								when visitbymonth.day_12 isnull or visitbymonth.day_12='0' or visitbymonth.day_12='1'  or visitbymonth.day_12='10' then 5
								else visitbymonth.day_12
							end,
							case 
								when visitbymonth.day_13 isnull or visitbymonth.day_13='0' or visitbymonth.day_13='1'  or visitbymonth.day_13='10' then 5
								else visitbymonth.day_13
							end,
							case 
								when visitbymonth.day_14 isnull or visitbymonth.day_14='0' or visitbymonth.day_14='1'  or visitbymonth.day_14='10' then 5
								else visitbymonth.day_14
							end,
							case 
								when visitbymonth.day_15 isnull or visitbymonth.day_15='0' or visitbymonth.day_15='1'  or visitbymonth.day_15='10' then 5
								else visitbymonth.day_15
							end,
							case 
								when visitbymonth.day_16 isnull or visitbymonth.day_16='0' or visitbymonth.day_16='1'  or visitbymonth.day_16='10' then 5
								else visitbymonth.day_16
							end,
							case 
								when visitbymonth.day_17 isnull or visitbymonth.day_17='0' or visitbymonth.day_17='1'  or visitbymonth.day_17='10' then 5
								else visitbymonth.day_17
							end,
							case 
								when visitbymonth.day_18 isnull or visitbymonth.day_18='0' or visitbymonth.day_18='1'  or visitbymonth.day_18='10' then 5
								else visitbymonth.day_18
							end,
							case 
								when visitbymonth.day_19 isnull or visitbymonth.day_19='0' or visitbymonth.day_19='1'  or visitbymonth.day_19='10' then 5
								else visitbymonth.day_19
							end,
							case 
								when visitbymonth.day_20 isnull or visitbymonth.day_20='0' or visitbymonth.day_20='1'  or visitbymonth.day_20='10' then 5
								else visitbymonth.day_20
							end,
							case 
								when visitbymonth.day_21 isnull or visitbymonth.day_21='0' or visitbymonth.day_21='1'  or visitbymonth.day_21='10' then 5
								else visitbymonth.day_21
							end,
							case 
								when visitbymonth.day_22 isnull or visitbymonth.day_22='0' or visitbymonth.day_22='1'  or visitbymonth.day_22='10' then 5
								else visitbymonth.day_22
							end,
							case 
								when visitbymonth.day_23 isnull or visitbymonth.day_23='0' or visitbymonth.day_23='1'  or visitbymonth.day_23='10' then 5
								else visitbymonth.day_23
							end,
							case 
								when visitbymonth.day_24 isnull or visitbymonth.day_24='0' or visitbymonth.day_24='1'  or visitbymonth.day_24='10' then 5
								else visitbymonth.day_24
							end,
							case 
								when visitbymonth.day_25 isnull or visitbymonth.day_25='0' or visitbymonth.day_25='1'  or visitbymonth.day_25='10' then 5
								else visitbymonth.day_25
							end,
							case 
								when visitbymonth.day_26 isnull or visitbymonth.day_26='0' or visitbymonth.day_26='1'  or visitbymonth.day_26='10' then 5
								else visitbymonth.day_26
							end,
							case 
								when visitbymonth.day_27 isnull or visitbymonth.day_27='0' or visitbymonth.day_27='1'  or visitbymonth.day_27='10' then 5
								else visitbymonth.day_27
							end,
							case 
								when visitbymonth.day_28 isnull or visitbymonth.day_28='0' or visitbymonth.day_28='1'  or visitbymonth.day_28='10' then 5
								else visitbymonth.day_28
							end,
							case 
								when visitbymonth.day_29 isnull or visitbymonth.day_29='0' or visitbymonth.day_29='1'  or visitbymonth.day_29='10' then 5
								else visitbymonth.day_29
							end,
							case 
								when visitbymonth.day_30 isnull or visitbymonth.day_30='0' or visitbymonth.day_30='1'  or visitbymonth.day_30='10' then 5
								else visitbymonth.day_30
							end,
							case 
								when visitbymonth.day_31 isnull or visitbymonth.day_31='0' or visitbymonth.day_31='1'  or visitbymonth.day_31='10' then 5
								else visitbymonth.day_31
							end
					from childs 
					left join visitbymonth
					on childs.id_org=visitbymonth.id_org1 and 
						childs.id_group=visitbymonth.id_group1 and 
						 childs.iin=visitbymonth.iin1)
	select id_org, id_group, iin, 
			day_1, 
			day_2, 
			day_3,
			day_4, 
			day_5, 
			day_6,
			day_7, 
			day_8, 
			day_9,
			day_10, 
			day_11, 
			day_12,
			day_13, 
			day_14, 
			day_15,
			day_16, 
			day_17, 
			day_18,
			day_19, 
			day_20, 
			day_21,
			day_22, 
			day_23, 
			day_24,
			day_25,
			day_26, 
			day_27, 
			day_28,
			day_29, 
			day_30, 
			day_31
		from readytbl"""

	with connection.cursor() as cursor:
		cursor.execute(query)
		columns = [col[0] for col in cursor.description]
		result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

	return HttpResponse(json.dumps(result, default=str), content_type="application/json")