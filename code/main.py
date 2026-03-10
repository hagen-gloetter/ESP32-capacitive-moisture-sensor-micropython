# Written by hagen@gloetter.de 06.06.2023
"""
main.py — Production entry point for the ESP32 moisture/humidity/watermeter node.

Initialises all hardware peripherals, connects to WiFi and MQTT, then runs an
event loop that samples sensors and publishes values on three schedules:

* every ``interval_update`` seconds (publish on change only)
* every ``interval_force`` seconds (force-publish all values)
* every other tick (display-only refresh)

A hardware timer (Timer 1) polls the water meter every 200 ms so no pulses are
missed even while the main loop is sleeping.

MQTT topics published::

    <room>/humidity        — DHT11 relative humidity (%)
    <room>/temperature     — DHT11 temperature (°C)
    <room>/moisture        — capacitive soil moisture (%)
    watermeter/value       — accumulated water volume (L)

Hardware (ESP32):
    - OLED display  : SCL=GPIO 22, SDA=GPIO 21
    - DHT11         : GPIO 33
    - Moisture ADC  : GPIO 32
    - Reed contact  : GPIO 13 (pull-up)

Secrets files required on flash:
    - ``secrets_wifi.json``  : WiFi credentials
    - ``secrets_mqtt.json``  : MQTT broker credentials
    - ``room.txt``           : Room name used as MQTT topic prefix
"""

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
from machine import RTC
from machine import WDT  # Phase-2: hardware watchdog
import utime             # Phase-2: needed for backoff sleep
import class_humidity_sensor
import class_capacitive_soil_moisture_sensor
import class_oled_display
import class_wifi_connection
import class_watermeter
import class_webserver
from time import localtime
import class_ntp

# https://www.realpythonproject.com/3-ways-to-store-and-read-credentials-locally-in-python/
# generate a file called .env
# in this Dir with this content:
# secretUser = "tasmota"
# secretPass = "totalsecret"
# secretHost = "iobroker.fritz.box"
# secretPort = "1883" # 1886

# init debug output
debugmode = False
debuglevel = 1
timermode = False  # timermode=True -> run via timer False run in main loop
publish_data = 0

print("Main started")
oled = class_oled_display.OledDisplay()
oled.displayText(0, "Main started")


def debug(msg, level):
    global debuglevel
    if level <= debuglevel:
        print(msg)
        oled.displayText(5, "D:" + str(msg))


print("Setup Wifi")
global wifi
wifi = class_wifi_connection.WifiConnect()
(wifi_status, wifi_ssid, wifi_ip) = wifi.connect()

print("Get Time")
ntp = class_ntp.NTPClock()
ntp.sync_time(wifi)

# get room if possible
room = "debugroom"
roomfn = "room.txt"
try:
    with open(roomfn, "r") as f:
        room = str(f.readline().rstrip())
        f.close()
except Exception as e:
    print(f"Failed to open {roomfn}")
    with open(roomfn, "w") as f:
        f.write(room)
if debugmode == True:  # Wenn Debug mode, dann in den DebugRaum loggen
    room = "debugroom"
print("ROOM = " + str(room))

# Setup MQTT
MQTT_BACKOFF_MAX = 6  # Max reconnect delay in seconds — must be < WDT timeout
with open("secrets_mqtt.json") as f:  # BUG-06 fixed: use context manager
    mqtt_json = ujson.load(f)
broker = mqtt_json["secretHost"]
port = mqtt_json["secretPort"]
username = mqtt_json["secretUser"]
password = mqtt_json["secretPass"]
# topic_basename = b"debugroom"
topic_basename = str.encode(room)
topicHumidity = topic_basename + b"/humidity"
topicTemperature = topic_basename + b"/temperature"
topicMoisture = topic_basename + b"/moisture"
topicWater = b"watermeter/value"  # production
if debugmode:  # BUG-05 fixed: was `if debug == True:` (debug is a function, not a variable)
    topicWater = topic_basename + b"/watermeter/value"  # test

print("brokerHost:Port = " + broker + " " + str(port))
print("user = " + username)
client_id = "mqtt-watermeter"

# init MQTT
debug("start connect_mqtt", 1)
myMqttClient = MQTTClient("mqtt-watermeter", broker, port, username, password)
_backoff = 1
while True:  # Phase-2: connect with exponential backoff
    try:
        myMqttClient.connect()
        _backoff = 1
        break
    except Exception as e:
        print(f"MQTT connect failed: {e}, retrying in {_backoff}s")
        utime.sleep(_backoff)
        _backoff = min(_backoff * 2, MQTT_BACKOFF_MAX)
myMqttClient.sock.settimeout(0.5)  # Phase-2: non-blocking socket

debug("start oled,moisture,temparature, watermeter", 1)
myMoistureSensor = class_capacitive_soil_moisture_sensor.MoistureSensor()
myHumiditySensor = class_humidity_sensor.HumiditySensor()
myWaterMeter = class_watermeter.Watermeter()

errorcount = 0   # BUG-04 fixed: initialize before publishMqtt can reference them
running = True   # BUG-04 fixed

# Functions


def publishMqtt(myMqttClient, topic, value):
    """
    Publish a single value to an MQTT topic; track consecutive errors.

    Args:
        myMqttClient: Connected ``umqtt.robust.MQTTClient`` instance.
        topic (bytes): MQTT topic bytes, e.g. ``b"room/humidity"``.
        value: Sensor reading; converted to str before publishing.
    """
    global errorcount
    global running
    debug("start publishMqtt", 1)
    debug(f"start publishMqtt topic={topic} value={value}", 1)

    try:
        result = myMqttClient.publish(topic, str(value))
    except Exception as e:  # BUG-18 fixed: typed except
        print(f"Failed to send message {value} to topic {topic}: {e}")
        errorcount += 1
        if errorcount > 1500:  # 0,2s*5 * 5*60s
            # break the loop and reconnect
            running = False
    else:
        print(f"Send `{value}` to topic `{topic}`")
        errorcount = 0


def sensor_timer(timer0):
    get_sensor_input("display_only")  # BUG-08 fixed: required argument was missing


def timer_watermeter(timer1):
    myWaterMeter.getWaterCount()  # has to be done every 200ms to not miss a signal
    oled.displayText(0, "" + str(ntp.get_time()) + "")


def get_watermeter():
    watercounter = myWaterMeter.getWaterCount()
    oled.displayText(4, "Water: " + str(watercounter) + "")
    # do not set water as it is a counter


def get_moisture():
    debug("get_moisture called", 0)
    oldmoisture = myMoistureSensor.get_oldmoisture()
    moisture = myMoistureSensor.get_moisture()
#    oled.displayText(4, "Moisture: " + str(moisture) + "%")
    if oldmoisture != moisture:
        publishMqtt(myMqttClient, topicMoisture, moisture)


def get_sensor_input(publish_data):
    """
    Read all sensors, optionally publish to MQTT, and update the OLED display.

    Args:
        publish_data (str): Control string:
            ``"force"``        – publish all values unconditionally,
            ``"update"``       – publish only values that changed since last call,
            ``"display_only"`` – update OLED only, no MQTT publish.
    """
    debug(f"get_sensor_input called {publish_data}", 5)  # BUG-09 fixed: f-string avoids TypeError when publish_data is non-str
    (wifi_status, wifi_ssid, wifi_ip) = wifi.check_connection()
    # get HumidityAndTemperature
    oldHumidity = myHumiditySensor.get_oldhumidity()
    oldTemperature = myHumiditySensor.get_oldtemperature()
    oldmoisture = myMoistureSensor.get_oldmoisture()
    oldwatercount = myWaterMeter.getoldWaterCount()
    watercounter = myWaterMeter.getWaterCount()
    (temperature, humidity) = myHumiditySensor.get_humidity_and_temperature()
    moisture = myMoistureSensor.get_moisture()
    print(f"oldHumidity    {oldHumidity}    \thumidity     {humidity}")
    print(f"oldTemperature {oldTemperature} \ttemperature  {temperature}")
    print(f"oldwatercount  {oldwatercount}  \twatercounter {watercounter}")

    if publish_data != "display_only":
        # no update if display only ohterwise we get no more data to mqtt
        myHumiditySensor.set_oldhumidity(humidity)
        myHumiditySensor.set_oldtemperature(temperature)
        myMoistureSensor.set_oldmoisture(moisture)
        
    if publish_data == "force":
        publishMqtt(myMqttClient, topicHumidity, humidity)
        publishMqtt(myMqttClient, topicTemperature, temperature)
        publishMqtt(myMqttClient, topicMoisture, moisture)
        publishMqtt(myMqttClient, topicWater, watercounter)
    elif publish_data == "update":
        if oldHumidity != humidity:
            publishMqtt(myMqttClient, topicHumidity, humidity)
        if oldTemperature != temperature:
            publishMqtt(myMqttClient, topicTemperature, temperature)
        if oldmoisture != moisture:
            publishMqtt(myMqttClient, topicMoisture, moisture)
        #if oldwatercount != watercounter:
        #   publishMqtt(myMqttClient, topicWater, watercounter)
    else:
        # no mqtt just display-update
        pass
    # display sensor data
    th_line = f'T: {temperature:02d}C | H: {humidity:02d}%'
    oled.displayText(1, str(wifi_status) + ": " + str(wifi_ssid))
    oled.displayText(2, th_line)
    oled.displayText(3, "Water: " + str(watercounter) + "")
#    oled.displayText(4, "Moisture: " + str(moisture) + "%")
    oled.displayText(4, "" + str(wifi_ip) + "")
#    oled.displayText(5, "Debug: " + str(debuglevel) + " " + str(publish_data))


if timermode == True:
    time.sleep(2)
    debug("starting timermode", 1)
    global timer0
    timer0 = Timer(0)
    timer0.init(period=1000, mode=Timer.PERIODIC, callback=get_sensor_input)
#
# run always in timer mode otherwide we lose values
debug("starting watertimer", 1)
global timer1
timer1 = Timer(1)
timer1.init(period=200, mode=Timer.PERIODIC, callback=timer_watermeter)

apache = class_webserver.Webserver()

# Phase-2: start WDT after all hardware init; 8 s timeout > max loop time
wdt = WDT(timeout=8000)


def stop_all():
    global apache
    apache.stop_webserver()
    timer0.deinit()
    myMqttClient.disconnect()
    wifi.disconnect()


def kill():
    stop_all()


if __name__ == "__main__":
    if timermode == False:
        pass
    interval = 1           # Main loop tick in seconds
    interval_update = 30   # Publish on change interval in seconds  (BUG-19 fixed: removed duplicate dead line)
    interval_force = 10*60 # Force publish interval in seconds
    cnt = 0
    while True:
        wdt.feed()  # Phase-2: feed WDT at start of every iteration
        time.sleep(interval)
        cnt += interval
        if cnt % interval_force == 0:
            get_sensor_input("force")
            print("Sensor Update FORCE")
            cnt=0
        elif cnt % interval_update == 0:
            print("Sensor Update CHANGE")
            get_sensor_input("update")
        else:
            get_sensor_input("display_only")

    pass
