# Flask
from flask import Flask, request
from flask import redirect, url_for

# Video parsing
import cv2
import sys

# Celery
from celery import Celery
from worker import work_frame
from kombu import Queue, Exchange

# Tools
import argparse
import json
from pprint import pprint
import datetime
import logging

import os
import glob

# Print to console with colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Flask server initialize
app = Flask(__name__)
# Logging info disable (only warnings/errors)
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

def main(max_persons):
    pass

# When video is uploaded to server by client
@app.route('/', methods=['POST'])
def upload_file():

    global frames_to_wait_for

    file = request.files['file']
    print("Recieved file -> " + bcolors.OKBLUE + str(file.filename) + bcolors.ENDC)
    print(bcolors.OKBLUE + "Saving frames for serving..."+ bcolors.ENDC)

    # Separate video into jpg frames, save them to /static for direct serving and send references to workers
    vidcap = cv2.VideoCapture(file.filename)
    success,image = vidcap.read()
    count = 0
    while (success and count < 15):
        ref_file = "static/video_" + str(file.filename) + "_frame_" + str(count) + ".jpg"
        cv2.imwrite(ref_file, image)
        success,image = vidcap.read()

        frames_to_wait_for += 1

        work_frame.delay(str(file.filename), count)
        count+=1
    print(bcolors.OKGREEN + "Done!" + bcolors.ENDC + "\n")
    return f"Video uploaded to server.\n"

# When frame returns from worker
@app.route('/return', methods=['POST'])
def test():
    global frames_to_wait_for
    global frames_arrived
    global max_people_limit

    frames_arrived += 1
    
    # If the max people limit was hit in this frame, print that info in the server console
    if request.json["people_detected"] > max_people_limit:
        print(bcolors.WARNING + "Frame " + str(request.json["frame_no"]) + ": " + str(request.json["people_detected"]) + " <person> detected" + bcolors.ENDC)

    # Update final_info -> dict with statistics to present in the end of processing.

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
    
    # When the waiting line is empty, prepare and print statistics
    if (frames_arrived == frames_to_wait_for):
        print('\n')
        print("Processed frames: " + str(final_info["proc_frames"]))
        print("Average processing time per frame: " + str(int(final_info["tot_time"]/final_info["proc_frames"])) + "ms")
        print("Person objects detected: " + str(final_info["people_detected"]))
        final_info["total_classes_found"] = len(final_info["classes_dict"])
        print("Total classes detected: " + str(final_info["total_classes_found"]))
        new_dict = {k: v for k, v in sorted(final_info["classes_dict"].items(), key=lambda item: item[1])} #Ordered dict
        new_list = list(new_dict.keys()) #Ordered list from ordered dict
        print("Top 3 objects detected:",end=' ')
        for i in range(len(new_list)):
            if (i==2):
                print(new_list[len(new_list)-(i+1)])
                break
            else:
                print(new_list[len(new_list)-(i+1)], end=', ')
        print('\n')

        files = glob.glob('static/*.jpg')
        for f in files:
            os.remove(f)

    return "Image recieved by server."


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

    # As frames are sent to broker, frames_to_wait_for is incremented. As frames return from workers, frames_arrived is incremented.
    # It's time to print the final statistics when frames_to_wait_for = frames_arrived.
    frames_to_wait_for = 0
    frames_arrived = 0

    app.run()
