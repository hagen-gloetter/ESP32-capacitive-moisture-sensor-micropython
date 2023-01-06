# Written by hagen@gloetter.de 06.06.2023
# 

# Setup da stuff
# Micropython:
# in der REPL-Console
# import upip
# upip.install('micropython-umqtt.robust')
# upip.install('micropython-umqtt.simple')

# Pins used
# OLED Display 
#       scl = 22
#       sda = 21
# HumiditySensor dht11
#       pin = 33
# MoistureSensor
#       pin = 32
# Reed-Contact 
#       pin = 13


import time
import sys
import random
import os
import ujson
from umqtt.robust import MQTTClient
from machine import Pin
from machine import Timer
import class_humidity_sensor
import class_capacitive_soil_moisture_sensor
import class_oled_display
import class_wifi_connection
import class_watermeter

# https://www.realpythonproject.com/3-ways-to-store-and-read-credentials-locally-in-python/
# generate a file called .env
# in this Dir with this content:
# secretUser = "tasmota"
# secretPass = "totalsecret"
# secretHost = "iobroker.fritz.box"
# secretPort = "1883" # 1886

# init debug output
debuglevel = 0
timermode = False  # timermode=True -> run via timer False run in main loop
periodic_message = 0


def debug(msg, level):
    global debuglevel
    if level <= debuglevel:
        print(msg)


# Setup Wifi
global wifi
wifi = class_wifi_connection.WifiConnect()
(wifi_status, wifi_ssid, wifi_ip) = wifi.connect()

# Setup MQTT
mqtt_json = ujson.load(open("secrets_mqtt.json"))
broker = mqtt_json["secretHost"]
port = mqtt_json["secretPort"]
username = mqtt_json["secretUser"]
password = mqtt_json["secretPass"]
topic_basename = b"debugroom"
topicHumidity = topic_basename + b"/humidity"
topicTemperature = topic_basename + b"/temperature"
topicMoisture = topic_basename + b"/moisture"
topicWater = b"watermeter/value" # production
topicWater = topic_basename + b"watermeter/value" # test

print("brokerHost:Port = " + broker + " " + str(port))
print("user = " + username)
client_id = "mqtt-watermeter"

# init MQTT
debug("start connect_mqtt", 1)
myMqttClient = MQTTClient("mqtt-watermeter", broker, port, username, password)
myMqttClient.connect()

debug("start oled,moisture,temparature, watermeter", 1)
oled = class_oled_display.OledDisplay()
myMoistureSensor = class_capacitive_soil_moisture_sensor.MoistureSensor()
myHumiditySensor = class_humidity_sensor.HumiditySensor()
myWaterMeter = class_watermeter.Watermeter()

# Functions
def publishMqtt(myMqttClient, topic, value):
    global errorcount
    global running
    debug("start publishMqtt", 1)
    debug(f"start publishMqtt topic={topic} value={value}", 1)

    try:
        result = myMqttClient.publish(topic, str(value))
    except:
        print(f"Failed to send message {value} to topic {topic}")
        errorcount += 1
        if errorcount > 1500:  # 0,2s*5 * 5*60s
            # break the loop and reconnect
            running = False
    else:
        print(f"Send `{value}` to topic `{topic}`")
        errorcount = 0


def sensor_timer(timer0):
    get_sensor_input()  # sont want args for sensor call, as i also call it from main

def get_watermeter(timer1):
    myWaterMeter.getWaterCount() # has to be done every 200ms to not miss a signal    


def get_sensor_input():
    debug("get_sensor_input called", 0)
    global periodic_message
    list = wifi.check_connection()
    if debuglevel > 2:
        for item in list:
            print(item)
    # get HumidityAndTemperature
    oldHumidity = myHumiditySensor.get_oldhumidity()
    oldTemperature = myHumiditySensor.get_oldtemperature()
    oldmoisture = myMoistureSensor.get_oldmoisture()
    oldwatercount = myWaterMeter.getoldWaterCount()

    (temperature, humidity) = myHumiditySensor.get_humidity_and_temperature()
    moisture = myMoistureSensor.get_moisture()
    watercounter = myWaterMeter.getWaterCount()

    periodic_message += 1
    if periodic_message == 10:  # publish every 10 minutes
        periodic_message = 0
        publishMqtt(myMqttClient, topicHumidity, humidity)
        publishMqtt(myMqttClient, topicTemperature, temperature)
        publishMqtt(myMqttClient, topicMoisture, moisture)
        publishMqtt(myMqttClient, topicWater, watercounter)
    else:  # publish on change
        if oldHumidity != humidity:
            publishMqtt(myMqttClient, topicHumidity, humidity)
        if oldTemperature != temperature:
            publishMqtt(myMqttClient, topicTemperature, temperature)
        if oldmoisture != moisture:
            publishMqtt(myMqttClient, topicMoisture, moisture)
        if oldwatercount != watercounter:
            publishMqtt(myMqttClient, topicWater, watercounter)
    myHumiditySensor.set_oldhumidity(humidity)
    myHumiditySensor.set_oldtemperature(temperature)
    myMoistureSensor.set_oldmoisture(moisture)
    # do not set water as it is a gauge

    # display sensor data
    oled.displayText(0, "Sensor readings:")
    oled.displayText(1, str(wifi_status) + ": " + str(wifi_ssid))
    oled.displayText(2, "Temperature: " + str(temperature) + "C")
    oled.displayText(3, "Humidity: " + str(humidity) + "%")
    oled.displayText(4, "Moisture: " + str(moisture) + "%")
    oled.displayText(5, "Water: " + str(watercounter) + "")
    oled.displayText(6, "Debug: " + str(debuglevel) + " " + str(periodic_message))


if timermode == True:
    time.sleep(2)
    debug("starting timers", 1)
    global timer0
    timer0 = Timer(0)
    timer0.init(period=60000, mode=Timer.PERIODIC, callback=get_sensor_input)

    timer1 = Timer(1)
    timer1.init(period=200, mode=Timer.PERIODIC, callback=get_watermeter)


def stop_all():
    timer0.deinit()
    myMqttClient.disconnect()
    wifi.disconnect()


def kill():
    stop_all()


if __name__ == "__main__":
    if timermode == False:
        while True:
            get_sensor_input()
            time.sleep(10)

    pass
