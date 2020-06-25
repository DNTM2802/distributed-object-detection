# Video parsing
import cv2
import sys

# Celery
from celery import Celery
from celery import bootsteps
from celery.bin import Option
import celeryconfig

# Object Detection
import numpy as np
import core.utils as utils
import tensorflow as tf
from core.yolov3 import YOLOv3, decode
from core.config import cfg
from PIL import Image

# Tools
import json
import time
import requests
import datetime

# Celery configuration
app = Celery('frame_works')
app.config_from_object(celeryconfig) # Configs file

# Celery arguments -> server and port
app.user_options['worker'].add(
    Option('--server', default='127.0.0.1')
)
app.user_options['worker'].add(
    Option('--port', default='5000')
)

server_addr=""

class CustomArgs(bootsteps.Step):

    def __init__(self, worker, server, port, **options):
        global server_addr
        print("\nSERVER -> " + str(server))
        print("PORT -> " + str(port))

        server_str=""
        port_str=""

        if type(server) == list:
            server_str = server[0]
        else:
            server_str = server

        if type(port) == list:
            port_str = port[0]
        else:
            port_str = port
            
        server_addr = "http://" + server_str + ":" + port_str + "/"
        print("\nSERVER ADDRESS -> " + server_addr)

app.steps['worker'].add(CustomArgs)

flag = True
input_size   = 416

# CELERY TASK
@app.task()
def work_frame(filename, count):
    global flag,model,server_addr,input_size

    start_time = datetime.datetime.now()

    # GET frame from server by server /static reference
    video_id = "video_" + str(filename) + "_frame_" + str(count) + ".jpg"
    ref_file = "static/" + video_id
    response = requests.get(server_addr + ref_file)

    # Image transformation to accepted format
    arr = np.asarray(bytearray(response.content), dtype=np.uint8)
    original_image = cv2.imdecode(arr, -1)
    
    ###### OBJECT DETECTION CODE #######

    # Read class names
    class_names = {}
    with open(cfg.YOLO.CLASSES, 'r') as data:
        for ID, name in enumerate(data):
            class_names[ID] = name.strip('\n')

    # Setup tensorflow, keras and YOLOv3

    original_image      = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
    original_image_size = original_image.shape[:2]

    image_data = utils.image_preporcess(np.copy(original_image), [input_size, input_size])
    image_data = image_data[np.newaxis, ...].astype(np.float32)
  
    if flag:
        input_layer  = tf.keras.layers.Input([input_size, input_size, 3])
        feature_maps = YOLOv3(input_layer)
        bbox_tensors = []
        for i, fm in enumerate(feature_maps):
            bbox_tensor = decode(fm, i)
            bbox_tensors.append(bbox_tensor)
        model = tf.keras.Model(input_layer, bbox_tensors)
        utils.load_weights(model, "./yolov3.weights")
        flag = False
    
    pred_bbox = model.predict(image_data)
    pred_bbox = [tf.reshape(x, (-1, tf.shape(x)[-1])) for x in pred_bbox]
    pred_bbox = tf.concat(pred_bbox, axis=0)

    bboxes = utils.postprocess_boxes(pred_bbox, original_image_size, input_size, 0.3)
    bboxes = utils.nms(bboxes, 0.45, method='nms')

    # We have our objects detected and boxed, lets move the class name into a list
    objects_detected = []
    for x0,y0,x1,y1,prob,class_id in bboxes:
        objects_detected.append(class_names[class_id])

    ### END OF OBJECT DETECTION CODE ###

    print(objects_detected)
    
    final_time = datetime.datetime.now() - start_time
    
    # Elaborate json with frame info and post to server in /return route
    final_dict={}
    people_count=0
    
    for obj in objects_detected:
        if str(obj) == "person":
            people_count+=1
        if str(obj) in final_dict:
            final_dict[str(obj)] += 1
        else:
            final_dict[str(obj)] = 1
    
    final_json = {
        "video_id":filename, 
        "frame_no":count, 
        "processing_time":str(final_time),
        "people_detected":people_count,
        "objects_detected":json.dumps(final_dict)
    }
    
    requests.post(server_addr + "return", json=final_json)
    return "\nDONE frame n. " + str(count) + "of video " + filename + "!\n"

