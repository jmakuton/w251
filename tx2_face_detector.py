import numpy as np
import cv2 as cv2
import time
import paho.mqtt.client as mqtt

LOCAL_MQTT_HOST="mqtt_broker"
LOCAL_MQTT_PORT=1883
LOCAL_MQTT_TOPIC="face_topic"

def on_connect_local(client, userdata, flags, rc):
        print("connected to local broker with rc: " + str(rc))
        client.subscribe(LOCAL_MQTT_TOPIC)

local_mqttclient = mqtt.Client()
local_mqttclient.on_connect = on_connect_local
local_mqttclient.connect(LOCAL_MQTT_HOST, LOCAL_MQTT_PORT, 60)


face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# 0 correspond to the USB camera. The 1 is reserved for the TX2 onboard camera
cap = cv2.VideoCapture(0)

local_mqttclient.loop_start()
print("stream started")
message_index = 0
while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    # We don't use the color information, so might as well save space
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    img = cv2.imshow('frame', gray)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

    for (x,y,w,h) in faces:
        cropped_faces = gray[y:y+h,x:x+w]
        cv2.imshow("cropped", cropped_faces)
        
        rc, png = cv2.imencode('.png', cropped_faces)
        message = png.tobytes()


        stuff_in_string = "Shepherd %d " % (message_index)
        #local_mqttclient.publish(LOCAL_MQTT_TOPIC, stuff_in_string, qos=1, retain=False)
        local_mqttclient.publish(LOCAL_MQTT_TOPIC, payload = message, qos=1, retain=False)
        #local_mqttclient.publish(LOCAL_MQTT_TOPIC, bytearray(cv.imencode('.png', crop_faces)[1]), qos=1, retain = false)
        
    message_index = message_index +1
    time.sleep(5) 

local_mqttclient.loop_stop()
local_mqttclient.disconnect()
cap.release()
cv2.destroyAllWindows()