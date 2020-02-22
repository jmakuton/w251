import numpy as np
import cv2 as cv2
import time
import paho.mqtt.client as mqtt
import sys

LOCAL_MQTT_HOST="vsi_mqtt_broker"
LOCAL_MQTT_PORT=1883
LOCAL_MQTT_TOPIC="face_topic"
S3_MOUNT="/w251-face-images"

img_index = 0

def on_connect_local(client, userdata, flags, rc):
    print("connected to local broker with rc: " + str(rc))
    client.subscribe(LOCAL_MQTT_TOPIC)

def on_message_local(client, userdata, msg):
    try:
        global img_index
        
        #Decode the message back into an image
        msg_as_np = np.frombuffer(msg.payload, dtype='uint8')
        img  = cv2.imdecode(msg_as_np, flags=1)
        
        #Save the image into S3
        cv2.imwrite(S3_MOUNT + "/" + str(img_index) + ".png", img)
        print("Image nr. " + str(img_index) + " saved in S3")
        img_index = img_index + 1

    except:
        print("Unexpected error:", sys.exc_info()[0])

local_mqttclient = mqtt.Client()
local_mqttclient.on_connect = on_connect_local
local_mqttclient.on_message = on_message_local
local_mqttclient.connect(LOCAL_MQTT_HOST, LOCAL_MQTT_PORT, 60)

local_mqttclient.loop_forever()