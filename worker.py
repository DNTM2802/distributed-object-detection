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
from flask.json import jsonify
import base64
import datetime

app = Celery('frame_works',backend='rpc://', broker='pyamqp://guest@localhost//')

@app.task()
def work_frame(data):
    start_time = datetime.datetime.now()
    #original_image = np.array(json_string)
    response = json.loads(data)
    string = response['img']
    jpg_original = base64.b64decode(string)
    jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    original_image = cv2.imdecode(jpg_as_np, flags=1)
    
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
    final_time = datetime.datetime.now() - start_time
    obj_types = []
    final_dict={}
    person_count=0
    for obj in objects_detected:
        if str(obj) == "person":
            person_count+=1
        if str(obj) in obj_types:
            final_dict[str(obj)] += 1
        else:
            obj_types.append(str(obj))
            final_dict[str(obj)] = 1
    final_json = {"video_id":"some_id", "frame_no":response['frame_no'], "processing_time":str(final_time),"people_detected":person_count,"objects_detected":json.dumps(final_dict)}


    requests.post('http://127.0.0.1:5000/return', json=final_json)
    return "DONE frame n. " + str(response['frame_no']) + "!"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-address", help="server address", default="localhost")
    parser.add_argument("--server-port", help="server address port", default=3456)
    args = parser.parse_args()

    main(args.server_address, args.server_port)
