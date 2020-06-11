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
from kombu import Queue, Exchange
import logging

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

app = Flask(__name__)
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

def main(max_persons):
    pass

# When video is uploaded to server by client
@app.route('/', methods=['POST'])
def upload_file():

    global frames_to_wait_for
    global start_time

    file = request.files['file']
    print("Recieved file -> " + str(file.filename))
    vidcap = cv2.VideoCapture(file.filename)
    success,image = vidcap.read()
    count = 0
    while (success):
        ref_file = "static/video_" + str(file.filename) + "_frame_" + str(count) + ".jpg"
        cv2.imwrite(ref_file, image)
        success,image = vidcap.read()

        frames_to_wait_for += 1

        work_frame.delay(str(file.filename), count)
        count+=1
    start_time = datetime.datetime.now()
    return f"Video uploaded to server."

# When frame returns from worker
@app.route('/return', methods=['POST'])
def test():
    
    global frames_to_wait_for
    global frames_arrived
    global start_time
    global frames_max_people
    global max_people_found
    global max_people_limit

    frames_arrived += 1
    
    final_info["proc_frames"] +=1
    
    time = request.json["processing_time"]
    total_ms = float(time.split(":")[0])*3600000 + float(time.split(":")[1])*60000 + float(time.split(":")[2])*1000
    final_info["tot_time"] += total_ms
    
    final_info["people_detected"] += request.json["people_detected"]
    # print(request.json["people_detected"])
    # print(type(request.json["people_detected"]))
    # print(max_people_limit)
    # print(type(max_people_limit))
    if request.json["people_detected"] > max_people_limit:
        print(bcolors.WARNING + "Frame " + str(request.json["frame_no"]) + ": " + str(request.json["people_detected"]) + " <person> detected" + bcolors.ENDC)

    classes_obj = json.loads(request.json["objects_detected"])

    # Add found objects and respective counting to final stats dict
    for type_obj, count_obj in classes_obj.items():
        if type_obj in final_info["classes_dict"]:
            final_info["classes_dict"][type_obj] += count_obj
        else:
            final_info["classes_dict"][type_obj] = count_obj
    
    # When the waiting line is empty, prepare and print statistics
    if (frames_arrived == frames_to_wait_for):
        final_time = datetime.datetime.now() - start_time
        print('\n')
        print("Processed frames: " + str(final_info["proc_frames"]))
        print("Total time: " + str(final_time))
        print("Average processing time per frame: " + str(int(final_info["tot_time"]/final_info["proc_frames"])) + "ms")
        print("Person objects detected: " + str(final_info["people_detected"]))
        
        final_info["total_classes_found"] = len(final_info["classes_dict"])
        print("Total classes detected: " + str(final_info["total_classes_found"]))
        
        new_dict = {k: v for k, v in sorted(final_info["classes_dict"].items(), key=lambda item: item[1])}
        new_list = list(new_dict.keys())
        
        print("Top 3 objects detected:",end=' ')
        for i in range(len(new_list)):
            if (i==2):
                print(new_list[len(new_list)-(i+1)])
                break
            else:
                print(new_list[len(new_list)-(i+1)], end=', ')
        # print("Frames where found more than 12 people:")
        # pprint(str(frames_max_people))
        # print("Max people found:")
        # pprint(str(max_people_found))
        print('\n')

    return "Image recieved by server."

# @app.route('/max_people/<frame_info>', methods=['POST'])
# def max_people(frame_info):
#     global frames_max_people
#     frames_max_people.append(frame_info)
#     print(bcolors.WARNING + "Frame " + str(frame_info.split("_")[0]) + ": " + str(frame_info.split("_")[1]) + " <person> detected" + bcolors.ENDC)
#     return "Max pepole info recieved by server.."




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", help="maximum number of persons in a frame", default=10)
    args = parser.parse_args()
    main(args.max)
    
    # Final stats dict
    final_info = {
    "proc_frames":0,
    "tot_time":0.0,
    "people_detected":0,
    "total_classes_found":0,
    "classes_dict":{}
    }
    max_people_limit = int(args.max)
    print(max_people_limit)
    max_people_found = [0,""]
    frames_max_people = []
    frames_to_wait_for = 0
    frames_arrived = 0
    start_time = datetime.time(0, 0)
    app.run()
