# Install (Linux)

```
$ python3 -m venv venv
$ source venv/bin/activate
$ python -m pip install --upgrade pip
$ pip install -r requirements.txt
$ wget https://pjreddie.com/media/files/yolov3.weights
$ sudo apt-get install rabbitmq-server
```
 
# Enable RabbitMQ Management API
An optional tool to monitor the queues:
```
$ rabbitmq-plugins enable rabbitmq_management
$ sudo rabbitmqctl stop
$ sudo rabbitmq-server -detached
```
Monitor available at http://localhost:15672/


# Usage 1 - Run Script
```
$ ./run.sh X Y Z A
```
Where X is the number of workers, Y is the max people limit to trigger detection warning, Z the address of the server and A the port of the server.
Example:
```
$ ./run.sh 3 15 127.0.0.1 5000
```
This script will also open the **Flower Monitor for Celery** page and the **RabbitMQ Management** page in your browser.

To upload videos to the server (and inside venv), we provide two example videos in the root folder:
```
$ curl -F ‘video=@moliceiro.m4v’ http://localhost:5000
$ curl -F ‘video=@crosswalk.mp4’ http://localhost:5000
```
# Usage 2 - Manual
Inside the virtual environment, initialize the server:
```
python3 server.py
```
Optional argument: ``` --max X``` , where X is the max people limit to trigger detection warning. Default is 15.

To initialize a worker, run:
```
celery -A worker worker
```
Optional arguments:
```--loglevel=info``` - Detailed information in console.
```--server``` - Server address. Default is ```127.0.0.1```.
```--port``` - Server port. Default is ```5000```.
```-n``` - Worker name in the form ```NAME@%h```.

#### Flower Monitor Tool for Celery:
```celery flower -A worker --broker_url='amqp://guest:guest@localhost:5672/' --broker_api=http://guest:guest@localhost:15672```

Available at: http://localhost:5555/

#### RabitMQ Management Page:
Available at: http://localhost:15672/
Login: guest@guest.


