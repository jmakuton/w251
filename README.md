Jupyter Notebook
README-DRAFT
Last Checkpoint: a few seconds ago
(autosaved)
Current Kernel Logo
Python 3 
File
Edit
View
Insert
Cell
Kernel
Widgets
Help

# Homework 03 – w251 MIDS Spring 2020
​
___
​
We will build a lightweight IoT application pipeline with components running both on the edge (Nvidia Jetson TX2) and the cloud (a VM in Softlayer). The use case is to execute a face detection from the webcam on the TX2 and at the end of the pipeline, store it on a cloud storage. We will be using a microservice architecture to stay very modular and keep in mind that this should be able to run on low power edge devices.
​
We used the following MQTT topic: `face_topic` and we chose to use a QoS of 1 so we have a guarantee that a message (the face image) is delivered at least one time to the receiver. It is possible for the message to be sent or delivered multiple times but it is fine for our use case.
​
Link to the public storage to see face images after we ran the face-detector:
​
https://w251-face-images.s3.par01.cloud-object-storage.appdomain.cloud/5.png
​
​
### We will set up the cloud part first as it needs to be running before the TX2 part.
​
___
​
# Instructions to run on the CLOUD
​
## Cloud VSI creation
​
Create the VSI 
```
ibmcloud sl vs create --hostname=face-detector --domain=jacques.com --cpu=2 --memory=4096 --datacenter=par01 --os=UBUNTU_16_64 --san --disk=100 --key=XXXXXXX 
```
​
Check the IP address of the newly created VSI 
```
ibmcloud sl vs list 
```
​
Connect to that VSI 
```
ssh root@XXX.XXX.XXX.XXX 
```
​
Secure the server 
```
vi /etc/ssh/sshd_config 
PermitRootLogin prohibit-password 
PasswordAuthentication no 
```
​
Install Docker 
```
sudo apt-get update 
sudo apt install apt-transport-https ca-certificates 
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - 
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic test" 
sudo apt update 
sudo apt install docker-ce 
sudo docker run hello-world 
```
​
## Cloud Storage set up
​
Order a Cloud Object Storage named “w251” on cloud.ibm.com - it has to be a default type, not classic otherwise difficulties to make it public.\
Create a bucket named "w251-face-images" in the same region as all VSI (par01 for us).\
Create Service credentials.\
Open the "View credentials" item to see "Access & Permissions" and save our `<Access Key ID>` and `<Secrete Access Key>`.
​
Install the IBM Cloud Storage (mainly following IBM cloud documentation https://cloud.ibm.com/docs/infrastructure/network-attached-storage?topic=network-attached-storage-MountCOSs3fuse)
​
```
sudo apt-get upgrade
sudo apt-get install automake autotools-dev fuse g++ git libcurl4-openssl-dev libfuse-dev libssl-dev libxml2-dev make pkg-config
```
​
Install s3fs-fuse
```
apt-get install s3fs
```
​
Store credentials in a specific file and location (that will be read by the command later automatically)
```
echo Access_Key_ID:Secret_Access_Key > ~/.passwd-s3fs
```
​
Secure that file
```
sudo chmod 600 ~/.passwd-s3fs
```
​
Create the directory that we want to mount the S3 bucket to
```
sudo mkdir /mnt/w251-face-images
```
​
And then we mount the bucket using (we use the public endpoint for this bucket)
```
sudo s3fs w251-face-images /mnt/w251-face-images -o url=http://s3.par01.cloud-object-storage.appdomain.cloud
```
​
We test the proper mounting by navigating to /mnt/w251-face-images and create a file there. 
​
​
## Cloud Docker bridge
​
Create a bridge: 
```
sudo docker network create --driver bridge cloud-hw03 
```
​
Check the bridge 
```
sudo docker network ls 
sudo docker network inspect cloud-hw03 
```
​
​
​
## Cloud Mosquitto Broker
​
Create an ubuntu linux - based mosquitto broker: 
Build the image 
```
sudo docker build -t vsi_mqtt_broker -f Dockerfile_vsi_mqtt_broker . 
```
​
Run container and launch broker 
```
sudo docker run --rm --name vsi_mqtt_broker --network cloud-hw03 -p 1883:1883 -ti vsi_mqtt_broker bash 
```
​
Launch the cloud broker 
```
/usr/sbin/mosquitto 
```
​
## Cloud Mosquitto Receiver
​
Create an ubuntu linux - based mosquitto receiver: 
Build the image 
```
sudo docker build -t vsi_mqtt_receiver -f Dockerfile_vsi_mqtt_receiver . 
```
Run container. Here we also add access to the mounted S3 w251-face-images. 
```
sudo docker run --rm --name vsi_mqtt_receiver --network cloud-hw03 -v "$(pwd)":/hw03 -v /mnt/w251-face-images:/w251-face-images -ti vsi_mqtt_receiver bash 
```
​
Navigate to /hw03 
Launch the cloud receiver 
​
```
python3 vsi_receiver.py 
```
​
___
​
# Instructions to run on the TX2 
​
## Docker bridge
​
Create a bridge:
```
sudo docker network create --driver bridge hw03 
```
​
Check the bridge 
```
sudo docker network ls 
sudo docker network inspect hw03 
```
​
## Mosquitto Broker
​
Create an alpine linux - based mosquitto broker:
​
Build the image 
```
sudo docker build -t mqtt_broker -f Dockerfile_tx2_mqtt_broker . 
```
​
Run container and launch broker 
```
sudo docker run --rm --name mqtt_broker --network hw03 -p 1883:1883 -ti mqtt_broker sh 
```
​
Launch broker 
```
/usr/sbin/mosquitto 
```
​
## Mosquitto Forwarder
​
Create an alpine linux - based mosquitto forwarder:
​
Build the image
```
sudo docker build -t mqtt_forwarder -f Dockerfile_tx2_mqtt_forwarder . 
```
​
Run container 
```
sudo docker run --rm --name mqtt_forwarder --network hw03 -v "$(pwd)":/hw03 -ti mqtt_forwarder sh 
```
​
Launch forwarder 
```
python3 tx2_forwarder.py 
```
​
## OpenCV Face Detector
​
Create an ubuntu linux - based face detector container:
​
Build the image 
```
sudo docker build -t face_detector -f Dockerfile_tx2_face_detector . 
```
​
Enable 
```
xhost + local:root
```
​
Run container
```
sudo docker run \ 
--user=root \ 
--env="DISPLAY" \ 
--volume="/etc/group:/etc/group:ro" \ 
--volume="/etc/passwd:/etc/passwd:ro" \ 
--volume="/etc/shadow:/etc/shadow:ro" \ 
--volume="/etc/sudoers.d:/etc/sudoers.d:ro" \ 
--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \ 
--rm --name face_detector --privileged --network hw03 -e DISPLAY=$DISPLAY --env QT_X11_NO_MITSHM=1 -v "$(pwd)":/hw03 -ti face_detector bash 
```
​
Need to run the following in the container before to avoid an error 
```
export NO_AT_BRIDGE=1
```
​
Launch the face detector 
```
python3 tx2_face_detector.py 
```