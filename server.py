import argparse
from flask import Flask, request
from flask import redirect, url_for
import cv2
import sys
from celery import Celery
from worker import work_frame
import json
import numpy as np
import codecs
import base64
from pprint import pprint
import datetime



app = Flask(__name__)

def main(max_persons):
    pass

@app.route('/', methods=['POST'])
def upload_file():
    global frames_to_wait_for
    file = request.files['file']
    file.save(file.filename)
    print(file)
    vidcap = cv2.VideoCapture(file.filename)
    success,image = vidcap.read()
    count = 0
    arr = []
    while (success):
        print(type(image))
        count += 1
        frames_to_wait_for += 1
        string = base64.b64encode(cv2.imencode('.jpg', image)[1]).decode()
        dictt = {
            'img': string,
            'frame_no' : count
        }

        res = work_frame.delay(json.dumps(dictt,ensure_ascii=False, indent=4))
        arr.append(res)
    return f"Thank you"

@app.route('/return', methods=['POST'])
def test():
    global frames_to_wait_for
    global frames_arrived
    frames_arrived += 1
    #pprint(request.json)
    final_info["proc_frames"] +=1
    time = request.json["processing_time"]
    total_ms = float(time.split(":")[0])*3600000 + float(time.split(":")[1])*60000 + float(time.split(":")[2])*1000
    final_info["tot_time"] += total_ms
    final_info["people_detected"] += request.json["people_detected"]
    classes_obj = json.loads(request.json["objects_detected"])
    for type_obj, count_obj in classes_obj.items():
        if type_obj in final_info["classes_dict"]:
            final_info["classes_dict"][type_obj] += count_obj
        else:
            final_info["classes_dict"][type_obj] = count_obj
    if (frames_arrived == frames_to_wait_for):
        print('\n')
        print("Processed frames: " + str(final_info["proc_frames"]))
        print("Average processing time per frame: " + str(int(final_info["tot_time"]/final_info["people_detected"])) + "ms")
        print("Person objects detected: " + str(final_info["people_detected"]))
        final_info["total_classes_found"] = len(final_info["classes_dict"])
        print("Total classes detected: " + str(final_info["total_classes_found"]))
        new_dict = {k: v for k, v in sorted(final_info["classes_dict"].items(), key=lambda item: item[1])}
        new_list = list(new_dict.keys())
        print("Top 3 objects detected: " + new_list[len(new_list)-1] + ", " + new_list[len(new_list)-2] + ", " + new_list[len(new_list)-3] + ".")
    print('\n')
    return "nice"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", help="maximum number of persons in a frame", default=10)
    args = parser.parse_args()
    main(args.max)

    final_info = {
    "proc_frames":0,
    "tot_time":0.0,
    "people_detected":0,
    "total_classes_found":0,
    "classes_dict":{}
    }
    frames_to_wait_for = 0
    frames_arrived = 0

    app.run()
