#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import dht11
import sys
import os
import ssl
import time
import datetime
import jwt
import paho.mqtt.client as mqtt

PROJECT_ID           = 'thermorecorder'
CLOUD_REGION         = 'asia-east1'
REGISTRY_ID          = 'rpi-sensor'
DEVICE_ID            = 'raspberrypi01'
ALGORITHM            = 'RS256'
PRIVATE_KEY_FILE     = 'rpi1.pem'
CA_CERTS             = 'roots.pem'
MQTT_BRIDGE_HOSTNAME = 'mqtt.googleapis.com'
MQTT_BRIDGE_PORT     = 8883

def thermometer(tm_handler):
    recorder = dict()
    while True:
        tm = tm_handler.read()
        if tm.is_valid():
            current_datetime = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            thi=0.81*tm.temperature+0.01*tm.humidity*(0.99*tm.temperature-14.3)+46.3
            recorder = "{{ 'time': {}, 'temperature': {}, 'humidity': {}, 'thi': {} }}".format(
                current_datetime, tm.temperature, tm.humidity, thi)
            return recorder

# mqtt client callback
def on_connect(unused_client, unused_userdata, unused_flags, rc):
    print('on_connect', mqtt.connack_string(rc))

def on_disconnect(unused_client, unused_userdata, rc):
    print('on_disconnect', mqtt.error_string(rc))

def on_publish(unused_client, unused_userdata, unused_mid):
    print('on_publish:', unused_mid)

def on_message(unused_client, unused_userdata, message):
    print('on_message')
    
def publish_to_IoTCore(data):
    mqtt_topic = '/devices/{}/events'.format(DEVICE_ID)
    client_id_f = 'projects/{}/locations/{}/registries/{}/devices/{}'
    client_id = client_id_f.format(PROJECT_ID, CLOUD_REGION, REGISTRY_ID, DEVICE_ID)
    client = mqtt.Client(client_id=client_id)
    
    token = {
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
        'aud': PROJECT_ID
    }
    
    with open(PRIVATE_KEY_FILE, 'r') as f:
        private_key = f.read()
        password = jwt.encode(token, private_key, algorithm=ALGORITHM)
        client.username_pw_set(username='unused' ,password=password)

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=CA_CERTS, tls_version=ssl.PROTOCOL_TLSv1_2)
    
    # Register message callbacks.
    client.on_connect    = on_connect
    client.on_publish    = on_publish
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    # Connect to the Google MQTT bridge.
    client.connect(MQTT_BRIDGE_HOSTNAME, MQTT_BRIDGE_PORT)
    client.loop_start()
    time.sleep(1)
    client.publish(mqtt_topic, data, qos=1)
    client.disconnect()
    client.loop_stop()
    
if __name__ == '__main__':
    try:
        # initialize GPIO
        GPIO.setwarnings(True)
        GPIO.setmode(GPIO.BCM)

        # get current thermo data
        dht11_handler = dht11.DHT11(pin=18)
        thermo_data = thermometer(dht11_handler)
        publish_to_IoTCore(thermo_data)
        
    except KeyboardInterrupt:
        GPIO.cleanup()
