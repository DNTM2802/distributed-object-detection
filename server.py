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
import datetime

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

    global start_time
    global videos_dict
    global final_info

    file = request.files['file']

    # Check if video is duplicated, and if it is, rename it. Save ammount of videos with each name in a dict
    
    # video identifier
    fileid = ""
    if str(file.filename) in videos_dict:
        filesplit = str(file.filename).split(".")
        fileid = filesplit[0] + str(videos_dict[str(file.filename)]) + "." + filesplit[1]
        videos_dict[str(file.filename)] += 1
    else:
        fileid = str(file.filename)
        videos_dict[str(file.filename)] = 1

    print("\nRecieved file -> " + bcolors.OKBLUE + str(fileid) + bcolors.ENDC)
    print(bcolors.OKBLUE + "Saving frames for serving and sending to queue..."+ bcolors.ENDC)

    # Separate video into jpg frames, save them to /static for direct serving and send references to workers
    vidcap = cv2.VideoCapture(file.filename)
    success,image = vidcap.read()
    count = 0
    while (success and count < 10):
        ref_file = "static/video_" + fileid + "_frame_" + str(count) + ".jpg"
        cv2.imwrite(ref_file, image)
        success,image = vidcap.read()

        work_frame.delay(fileid, count)
        count+=1
    
    # Create entry for this video in the infos dict. Save initial time and total frames to wait for.
    start_time = datetime.datetime.now()
    final_info[fileid] = {"total_frames":count,"start_time":start_time}

    print(bcolors.OKGREEN + "Done!" + bcolors.ENDC + "\n")
    return f"\nVideo uploaded to server.\n"

# When frame returns from worker
@app.route('/return', methods=['POST'])
def test():

    global max_people_limit
    global start_time
    global final_info

    # If the max people limit was hit in this frame, print that info in the server console
    if request.json["people_detected"] > max_people_limit:
        print(bcolors.WARNING + "Video " + str(request.json["video_id"]) +  ", Frame " + str(request.json["frame_no"]) + ": " + str(request.json["people_detected"]) + " <person> detected" + bcolors.ENDC)
    
    # Get infos from this frame to save in the infos dict
    fileid = request.json["video_id"]
    time = request.json["processing_time"]
    total_ms = float(time.split(":")[0])*3600000 + float(time.split(":")[1])*60000 + float(time.split(":")[2])*1000
    classes_obj = json.loads(request.json["objects_detected"])
    
    
    # Update infos dict -> dict with statistics to present in the end of processing each video.
    
    if "proc_frames" in final_info[fileid]:
        # Dict of dict already created
        final_info[fileid]["proc_frames"] +=1
        final_info[fileid]["tot_time"] += total_ms
        final_info[fileid]["people_detected"] += request.json["people_detected"]
    else:
        # Dict of dict not created, create it
        final_info[fileid]["proc_frames"] = 1
        final_info[fileid]["tot_time"] = total_ms
        final_info[fileid]["people_detected"] = request.json["people_detected"]
        final_info[fileid]["classes_dict"] = {}

    # Update top classes found
    for type_obj, count_obj in classes_obj.items():
        if type_obj in final_info[fileid]["classes_dict"]:
            final_info[fileid]["classes_dict"][type_obj] += count_obj
        else:
            final_info[fileid]["classes_dict"][type_obj] = count_obj
    
    # When total frames match processed frames, it's time to print the video info
    if (final_info[fileid]["proc_frames"] == final_info[fileid]["total_frames"]):
        # Final time
        final_time = datetime.datetime.now() - final_info[fileid]["start_time"]
        final_info[fileid]["end_time"] = final_time
        print('\n')
        print(bcolors.BOLD + "Video " + fileid + " fully processed." + bcolors.ENDC)
        print("Total time: " + str(final_time))
        print("Processed frames: " + str(final_info[fileid]["proc_frames"]))
        print("Average processing time per frame: " + str(int(final_info[fileid]["tot_time"]/final_info[fileid]["proc_frames"])) + "ms")
        print("Person objects detected: " + str(final_info[fileid]["people_detected"]))
        final_info[fileid]["total_classes_found"] = len(final_info[fileid]["classes_dict"])
        print("Total classes detected: " + str(final_info[fileid]["total_classes_found"]))
        new_dict = {k: v for k, v in sorted(final_info[fileid]["classes_dict"].items(), key=lambda item: item[1])} #Ordered dict
        new_list = list(new_dict.keys()) #Ordered list from ordered dict
        print("Top 3 objects detected:",end=' ')
        for i in range(len(new_list)):
            if (i==2):
                print(new_list[len(new_list)-(i+1)])
                break
            else:
                print(new_list[len(new_list)-(i+1)], end=', ')
        print('\n')

        # Delete frames of this video from /static, since theyre no longer needed
        ref_to_delete = request.json["video_id"].split("_")[0]
        files = glob.glob('static/video_' + ref_to_delete + "*")
        for f in files:
            os.remove(f)

    return "\nImage recieved by server.\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", help="maximum number of persons in a frame", default=10)
    args = parser.parse_args()
    main(args.max)
    
    # Final stats dict
    final_info = {}

    # Max people limit from arg
    max_people_limit = int(args.max)

    # Just initialize start time to use as global variable
    start_time = datetime.datetime.now()

    # Dict that saves the uploaded video names and eventual repetitions
    videos_dict={}

    app.run()
