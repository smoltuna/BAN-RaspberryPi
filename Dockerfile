FROM python:3.10

RUN apt-get update && apt-get install -y bluez dbus sudo libglib2.0-dev libcap2-bin


COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

EXPOSE 8501

#RUN ls -la /usr/local/lib

#RUN sudo setcap cap_net_raw+e  /usr/local/lib/python3.10/dist-packages/bluepy/bluepy-helper
#RUN sudo setcap cap_net_admin+eip  /usr/local/lib/python3.10/dist-packages/bluepy/bluepy-helper
#
COPY . ./wearable_camera
#
WORKDIR ./wearable_camera
#

RUN ["chmod", "+x", "entrypoint.sh"]

CMD ./entrypoint.sh




