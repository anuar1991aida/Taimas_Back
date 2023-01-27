from PIL import Image
import os
import os.path, time
import datetime


def childphoto():
    CurDateTime = datetime.datetime.today()
    #if not CurDateTime.hour == 11:
     #   print(CurDateTime)
     #   return

    count = 0

    path = "//192.168.5.22/FaceDastan/result/"
    patharh = "E:/arhive/"
    listOfFiles = os.listdir(path)
    for fileitem in listOfFiles:
        if os.path.isfile(path + fileitem):
            mas = fileitem.split('-')[0].split('_')
            org_id = mas[0]
            group_id = mas[1]
            group_id = group_id.replace('.jpg','')  #Если файл без "-1" тогда удаляем .jpg

            t = os.path.getmtime(path + fileitem)
            time = str(datetime.datetime.fromtimestamp(t)).split();
            nametime = time[0].replace('-', '')

            newpath = patharh + org_id + '/'
            direxist = os.path.isdir(newpath)
            if not direxist:
                os.mkdir(newpath)

            newpath = patharh + org_id + '/' + group_id + '/'
            direxist = os.path.isdir(newpath)
            if not direxist:
                os.mkdir(newpath)


            newpath = patharh + org_id + '/' + group_id + '/' + nametime + '/'
            direxist = os.path.isdir(newpath)
            if not direxist:
                os.mkdir(newpath)

            countphoto = 1
            #Получаем временный файл после записи
            image = Image.open(path +   fileitem)
            print("opened: " + path +   fileitem)
            newfileexist = os.path.exists(newpath + str(countphoto) + '.jpg')
            while newfileexist:
                countphoto = countphoto + 1
                newfileexist = os.path.exists(newpath + str(countphoto) + '.jpg')

            print("created: " + newpath + str(countphoto) + '.jpg')
            #Сохраним со сжатие
            image.save(newpath + str(countphoto) + '.jpg', quality=20, optimize=True)
            os.remove(path +   fileitem)


if __name__ == '__main__':
    childphoto()
