import argparse
import os
import time
import warnings
from datetime import datetime
import cv2
import numpy as np

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name
from django.db import connection

warnings.filterwarnings('ignore')
#conn = setting.connectdb()

#SAMPLE_IMAGE_PATH = "C:/Users/dastan/Desktop/FaceDastan/result/"
#FAKE_PATH = 'Anti_spoofing/Fake/'
#REAL_PATH = 'Anti_spoofing/Real/'

# Поскольку соотношение сторон видеопотока, полученного Android APK, составляет 3:4, чтобы соответствовать ему, соотношение сторон ограничено до 3:4.
# def check_image(image):
#     try:
#         height, width, channel = image.shape
#         if width/height != 3/4:
#             #print("Image is not appropriate!!!\nHeight/Width should be 4/3.")
#             return True
#         else:
#             return True
#     except:
#         return False

def test(image_name,image, model_dir, device_id):
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()
    #image = cv2.imread(image_name)
    #delited = image_name

    image_bbox = model_test.get_bbox(image)
    prediction = np.zeros((1, 3))
    test_speed = 0
    # суммировать прогноз по результату одной модели
    for model_name in os.listdir(model_dir):
        h_input, w_input, model_type, scale = parse_model_name(model_name)
        param = {
            "org_img": image,
            "bbox": image_bbox,
            "scale": scale,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        if scale is None:
            param["crop"] = False
        img = image_cropper.crop(**param)
        start = time.time()
        prediction += model_test.predict(img, os.path.join(model_dir, model_name))
        test_speed += time.time()-start

    # draw result of prediction
    label = np.argmax(prediction)
    value = prediction[0][label]/2
    if label == 1:
        #print("Image '{}' is Real Face. Скорость: {:.2f}.".format(image_name, value))
        result_text = "RealFace Score: {:.2f}".format(value)
        color = (255, 0, 0)
    else:
        #print("Image '{}' is Fake Face. Скорость: {:.2f}.".format(image_name, value))
        result_text = "FakeFace Score: {:.2f}".format(value)
        color = (0, 0, 255)
    #print("Скорость определение {:.2f} s".format(test_speed))
    # cv2.rectangle(
    #     image,
    #     (image_bbox[0], image_bbox[1]),
    #     (image_bbox[0] + image_bbox[2], image_bbox[1] + image_bbox[3]),
    #     color, 2)
    # cv2.putText(
    #     image,
    #     result_text,
    #     (image_bbox[0], image_bbox[1] - 5),
    #     cv2.FONT_HERSHEY_COMPLEX, 0.5*image.shape[0]/1024, color)
    if label != 1:
        return True
    else:
        return False    
        # format_ = os.path.splitext(image_name)[-1]
        # result_image_name = image_name.replace(format_, "_result" + format_).replace('imges_Ras/','')
        
        # num = 0
        # path = FAKE_PATH + result_image_name
        # fileexist = os.path.exists(path)
        # while fileexist:
        #      num = num + 1
        #      path = FAKE_PATH + result_image_name.replace(format_, str(num) + format_)
        #      fileexist = os.path.exists(path)
        
    #     Danye = cls.split('_')
    #     id_org = Danye[0]
    #     id_group = Danye[1]
    #     _list = Danye[2].replace('(','').replace(')','')
    #     children_list = _list.split('-')
        
    #     for i in children_list:
    #         if i != '':
    #             date = datetime.now().date()
    #             taim = datetime.now().time()
    #             cur = connection.cursor()
    #             cur.execute(f"SELECT status,iin From serviceback_visits WHERE id_org = '{id_org}' and id_group = '{id_group}' and datestatus = '{date}' and iin = '{i}';")
    #             #conn.commit()
    #             results = cur.fetchall()
    #             if len(results) == 0:
    #                 cur = connection.cursor()
    #                 cur.execute(f"INSERT INTO serviceback_visits(id_org,id_group,iin,status,datestatus,timestatus) VALUES ('{id_org}','{id_group}','{i}','10','{date}','{taim}')")
    #                 connection.commit()
    #             else:
    #                 cur = connection.cursor()
    #                 cur.execute(f"UPDATE serviceback_visits  SET status = '10' WHERE id_org = '{id_org}' and id_group = '{id_group}' and datestatus = '{date}' and iin = '{i}'")
    #                 connection.commit()


    #     cv2.imwrite(path, image)
    # else:
    #     format_ = os.path.splitext(image_name)[-1]
    #     result_image_name = image_name.replace(format_, "_result" + format_).replace('imges_Ras/','')
    #     num = 0
    #     path2 = REAL_PATH + result_image_name
    #     fileexist = os.path.exists(path2)
    #     while fileexist:
    #         num = num + 1
    #         path2 = REAL_PATH + result_image_name.replace(format_, str(num) + format_)
    #         fileexist = os.path.exists(path2)
        
    #     cv2.imwrite(path2, image)
    
    # #os.remove(delited)    

    
def startfilter(img,id_org,id_group,current_frame_face_name_list):
    desc = "test"
    namelist = ''
    model = 'resources/anti_spoof_models'
    device = 0
    test1 = 0
    for i in current_frame_face_name_list:
        if i == 'unknown':
            continue
        else:
            namelist = namelist + '' + i
    if namelist != '':
        imy = id_org + '-' + id_group + '-' + namelist
        try:
            result = test(imy,img,model,device)
            return result
        except:
            return None
    else:
        return None       

    
    # while True:
    #     myList = os.listdir('imges_Ras')
    #     #start = time.time()
    #     for cls in myList:
    #         #try:
    #         if cls != 'Thumbs.db':
    #                 test(f'imges_Ras/{cls}',model,device,cls)
    #         #except:
    #             #continue
    #     #test1 += time.time()-start
    #     #print("Время завершение {:.2f} s".format(test1))


if __name__ == '__main__':
    startfilter()


    
