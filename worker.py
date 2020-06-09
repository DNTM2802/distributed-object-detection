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

app = Celery('frame_works',backend='rpc://', broker='pyamqp://guest@localhost//')

@app.task()
def work_frame(count):
    json_string = json.dumps({"oi":"ola"})
    requests.post('http://127.0.0.1:5000/return', json=json_string)
    return "Results above for frame " + str(count)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-address", help="server address", default="localhost")
    parser.add_argument("--server-port", help="server address port", default=3456)
    args = parser.parse_args()

    main(args.server_address, args.server_port)
