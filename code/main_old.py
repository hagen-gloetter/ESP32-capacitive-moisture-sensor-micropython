# Setup da stuff
# Micropython:
# in der REPL-Console
# import upip
# upip.install('micropython-umqtt.robust')
# upip.install('micropython-umqtt.simple')

import time
import sys
import random
import os
import ujson
from umqtt.robust import MQTTClient
from machine import Pin
from machine import Timer
from humidity_sensor import get_humidity
import get_wifi_connection
import oled_display
# https://www.realpythonproject.com/3-ways-to-store-and-read-credentials-locally-in-python/
# generate a file called .env
# in this Dir with this content:
#secretUser = "tasmota"
#secretPass = "totalsecret"
#secretHost = "iobroker.fritz.box"
# secretPort = "1883" # 1886

# Setup MQTT
mqtt_json = ujson.load(open("secrets_mqtt.json"))
broker = mqtt_json["secretHost"]
port = mqtt_json["secretPort"]
username = mqtt_json["secretUser"]
password = mqtt_json["secretPass"]

topicHumidity = b"dungeon/humidity"
topicTemperature = b"dungeon/temperature"
topicWater = b"water"

print("brokerHost:Port = " + broker + " "+str(port))
print("user = "+username)
client_id = "mqtt-watermeter"
WaterLevelFn = "waterlevel.txt"

reed = Pin(13, Pin.IN, Pin.PULL_UP)
dht11 = Pin(33)
display_scl = Pin(22)
display_sda = Pin(21)
oled = oled_display.init_display(display_scl, display_sda)

debuglevel = 0

# Functions


def debug(msg, level):
    global debuglevel
    if level <= debuglevel:
        print(msg)


def increaseAndSaveWaterValue(water):
    debug(f"increaseAndSaveWaterValue {water}", 2)
    water += 2.5
    with open(WaterLevelFn, "w") as f:
        f.write("{0:0.1f}".format(water))
        f.close()
        return water


def connect_mqtt():
    global client
    debug("start connect_mqtt", 1)
    client = MQTTClient("mqtt-watermeter", broker, port, username, password)
    client.connect()


def publishMqtt(client, topic, value):
    global errorcount
    global running
    debug("start publishMqtt", 1)
    debug(f"start publishMqtt topic={topic} value={value}", 1)

    try:
        result = client.publish(topic, str(value))
    except:
        print(f"Failed to send message {value} to topic {topic}")
        errorcount += 1
        if errorcount > 1500:  # 0,2s*5 * 5*60s
            # break the loop and reconnect
            running = False
    else:
        print(f"Send `{value}` to topic `{topic}`")
        errorcount = 0


def doWater():
    global client
    global debounceCounter
    global water
    global errorcount
    global running
    debug("start doWater", 1)
    # do a schmitt trigger
    oldWater = water
    if (reed.value() == 0 and debounceCounter < 10):
        debounceCounter += 1
        if (debounceCounter == 10):
            water = increaseAndSaveWaterValue(water)
    elif (reed.value() == 1 and debounceCounter > 0):
        debounceCounter -= 1
        if (debounceCounter == 0):
            water = increaseAndSaveWaterValue(water)
    # send MQTT
    if (oldWater != water):
        publishMqtt(client, topicWater, water)


def doHumidityAndTemperature():
    global client
    global humidity
    global temperature
    global errorcount
    global running
    debug("start doHumidityAndTemperature", 1)
    oldHumidity = humidity
    oldTemperature = temperature
    (temperature, humidity) = get_humidity(dht11)
    if (oldHumidity != humidity):
        publishMqtt(client, topicHumidity, humidity)
    if (oldTemperature != temperature):
        publishMqtt(client, topicTemperature, temperature)


def WaterTimer(timer0):
    doWater()


def TemperatureTimer(timer1):
    doHumidityAndTemperature()


def WifiTimer(timer2):
    (wifi_status, wifi_ssid, wifi_ip) = check_wifi_connection()


def publish():
    global debounceCounter
    global water
    global temperature
    global humidity
    global errorcount
    global running
    debug("start publish", 1)
    debounceCounter = 0
    water = 0
    temperature = 0
    humidity = 0
    errorcount = 0
    # Read Watermeter Value from file
    with open(WaterLevelFn, "r") as f:
        water = float(f.readline().rstrip())
        f.close()
    (oldTemperature, oldHumidity) = get_humidity(dht11)
    time.sleep(2)
    debug("starting timers", 1)

    global timer0
    timer0 = Timer(0)
    timer0.init(period=2000, mode=Timer.PERIODIC, callback=TemperatureTimer)
    global timer1
    timer1 = Timer(1)
    timer1.init(period=200, mode=Timer.PERIODIC, callback=WaterTimer)
    global timer2
    timer2 = Timer(2)
    timer2.init(period=60000, mode=Timer.PERIODIC, callback=WifiTimer)


def stop_all():
    global client
    global timer0
    global timer1
    timer0.deinit()
    timer1.deinit()
    client.disconnect()
    import get_wifi_connection
    global wifi
    get_wifi_connection.disconnect_wifi()


def kill():
    stop_all()


if __name__ == '__main__':
    connect_mqtt()
    publish()
