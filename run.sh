#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "Please pass the number of workers you want to run as an argument!"
    exit 1
fi
if [ "$#" -ne 4 ]; then
    echo "Pass 4 arguments."
    exit 1
fi

source venv/bin/activate
for i in $(seq 1 $1); do
    x-terminal-emulator -e celery -A worker worker --loglevel=info -n woker$i@%h --server $3 --port $4
done

x-terminal-emulator -e python3 server.py --max $2
x-terminal-emulator -e celery flower -A worker --broker_url='amqp://guest:guest@localhost:5672/' --broker_api=http://guest:guest@localhost:15672/api/ 

xdg-open http://localhost:5555/
xdg-open http://localhost:15672/
