import argparse
from flask import Flask, request
from flask import redirect, url_for
import cv2
import sys
from celery import Celery
import json
import numpy as np
import core.utils as utils
import tensorflow as tf
from core.yolov3 import YOLOv3, decode
from core.config import cfg
from PIL import Image
import time
import requests
import datetime
import celeryconfig

app = Celery('frame_works')
app.config_from_object(celeryconfig)

@app.task()
def work_frame(filename, count):

    start_time = datetime.datetime.now()
    video_id = "video_" + str(filename) + "_frame_" + str(count) + ".jpg"
    ref_file = "static/" + video_id
    response = requests.get('http://127.0.0.1:5000/'+ ref_file)
    arr = np.asarray(bytearray(response.content), dtype=np.uint8)
    original_image = cv2.imdecode(arr, -1) # 'Load it as it is'
    
    # Read class names
    class_names = {}
    with open(cfg.YOLO.CLASSES, 'r') as data:
        for ID, name in enumerate(data):
            class_names[ID] = name.strip('\n')

    # Setup tensorflow, keras and YOLOv3
    input_size   = 416
    input_layer  = tf.keras.layers.Input([input_size, input_size, 3])
    feature_maps = YOLOv3(input_layer)

    original_image      = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
    original_image_size = original_image.shape[:2]

    image_data = utils.image_preporcess(np.copy(original_image), [input_size, input_size])
    image_data = image_data[np.newaxis, ...].astype(np.float32)

    bbox_tensors = []
    for i, fm in enumerate(feature_maps):
        bbox_tensor = decode(fm, i)
        bbox_tensors.append(bbox_tensor)

    model = tf.keras.Model(input_layer, bbox_tensors)
    utils.load_weights(model, "./yolov3.weights")

    pred_bbox = model.predict(image_data)
    pred_bbox = [tf.reshape(x, (-1, tf.shape(x)[-1])) for x in pred_bbox]
    pred_bbox = tf.concat(pred_bbox, axis=0)

    bboxes = utils.postprocess_boxes(pred_bbox, original_image_size, input_size, 0.3)
    bboxes = utils.nms(bboxes, 0.45, method='nms')

    # We have our objects detected and boxed, lets move the class name into a list
    objects_detected = []
    for x0,y0,x1,y1,prob,class_id in bboxes:
        objects_detected.append(class_names[class_id])
    print(objects_detected)
    final_time = datetime.datetime.now() - start_time
    final_dict={}
    person_count=0
    
    for obj in objects_detected:
        if str(obj) == "person":
            person_count+=1
        if str(obj) in final_dict:
            final_dict[str(obj)] += 1
        else:
            final_dict[str(obj)] = 1
    final_json = {
        "video_id":filename, 
        "frame_no":count, 
        "processing_time":str(final_time),
        "people_detected":person_count,
        "objects_detected":json.dumps(final_dict)
    }
    # if person_count > 12:
    #     requests.post('http://127.0.0.1:5000/max_people/' + str(count) + "_" + str(person_count))
    requests.post('http://127.0.0.1:5000/return', json=final_json)
    return "DONE frame n. " + str(count) + "of video " + filename + "!"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-address", help="server address", default="localhost")
    parser.add_argument("--server-port", help="server address port", default=3456)
    args = parser.parse_args()

    main(args.server_address, args.server_port)
