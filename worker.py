import argparse
from flask import Flask, request
from flask import redirect, url_for
import cv2
import sys
from celery import Celery
import json
import np


app = Celery('frame_works',backend='rpc://', broker='pyamqp://guest@localhost//')

@app.task
def work_frame(image):
    image = json.loads(image)
    image = np.array(image)
    return "Yes"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-address", help="server address", default="localhost")
    parser.add_argument("--server-port", help="server address port", default=3456)
    args = parser.parse_args()

    main(args.server_address, args.server_port)
