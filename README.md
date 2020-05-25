# Install

```
$ python3 -m venv venv
$ source venv/bin/activate
$ python -m pip install --upgrade pip
$ pip install -r requirements.txt
$ wget https://pjreddie.com/media/files/yolov3.weights
```
 
# Examples
```
$ python3 object_detect.py kite.jpg
$ python3 video2image.py moliceiro.m4v
```

# Update your fork
```
$ git remote add upstream https://github.com/detiuaveiro/CD_distributed_object_detection.git
$ git fetch upstream
$ git checkout master
$ git merge upstream/master
```
