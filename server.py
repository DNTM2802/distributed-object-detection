import argparse
from flask import Flask, request
from flask import redirect, url_for
import cv2
import sys
from celery import Celery
from worker import work_frame
import json


app = Flask(__name__)

def main(max_persons):
    pass

@app.route('/', methods=['POST'])
def upload_file():
    file = request.files['file']
    file.save(file.filename)
    print(file)
    vidcap = cv2.VideoCapture(file.filename)
    success,image = vidcap.read()
    count = 0
    arr = []
    while (success and count < 400):
        print(type(image))
        count += 1
        work_frame.delay(count)
    print(arr)
    return f"Thank you"

@app.route('/return', methods=['POST'])
def test():
    print(request.json)
    return "nice"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", help="maximum number of persons in a frame", default=10)
    args = parser.parse_args()
    main(args.max)
    app.run()
