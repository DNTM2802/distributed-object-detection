import argparse
from flask import Flask, request
from flask import redirect, url_for
import cv2
import sys


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
    while success:
        success,image = vidcap.read()
        print(count)
        count += 1
    return f"Thank you"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", help="maximum number of persons in a frame", default=10)
    args = parser.parse_args()
    main(args.max)
    app.run()
