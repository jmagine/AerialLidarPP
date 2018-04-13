FROM ubuntu:16.04

RUN apt-get update && apt-get install python3 python3-pip python3-dev libpng-dev libfreetype6-dev pkg-config -y
RUN python3 -m pip install --upgrade pip
RUN apt-get install libgdal-dev gdal-bin -y
RUN apt-get install qtbase5-dev -y
ADD . .
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install rasterio

CMD python3 gui.py
