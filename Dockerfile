FROM ubuntu:16.04
ADD . .

RUN apt-get update && apt-get install python3 python3-pip python3-dev -y
RUN python3 -m pip install -r requirements.txt

CMD python3 gui.py
