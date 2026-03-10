import time
"""
class_mqtt.py — MQTT helper wrapper around ``umqtt.robust.MQTTClient``.

Loads broker credentials from a JSON secrets file and exposes a simplified
publish interface with error counting.

Usage::

    from class_mqtt import MQTT
    m = MQTT()
    client = m.connect()
    m.publish(client, b"room/humidity", 55)

Secrets file (``secrets_mqtt.json``)::

    {"secretHost": "broker.local", "secretPort": 1883,
     "secretUser": "user",        "secretPass": "pass"}
"""
import sys
import random
import os
import ujson
from umqtt.robust import MQTTClient
from machine import Pin
from machine import Timer


class MQTT:
    """Class to connect your ESP32 to a MQTT Server."""

    def __init__(self, mqtt_json_file="secrets_mqtt.json", client_id="mqtt-watermeter"):
        # Setup MQTT
        with open(mqtt_json_file) as f:  # BUG-06 fixed: use context manager
            self.mqtt_json = ujson.load(f)
        self.broker = self.mqtt_json["secretHost"]
        self.port = self.mqtt_json["secretPort"]
        self.username = self.mqtt_json["secretUser"]
        self.password = self.mqtt_json["secretPass"]
        self.client_id = client_id  # BUG-03 fixed: was missing
        self.client = None
        self.errorcount = 0
        self.connection_running = True
        print("brokerHost:Port = " + self.broker + " " + str(self.port))
        print("user = " + self.username)

    def connect(self):
        """
        Create and connect an MQTTClient instance.

        Returns:
            umqtt.robust.MQTTClient: The connected client object.
        """
        print("start connect_mqtt", 1)
        self.client = MQTTClient(
            self.client_id, self.broker, self.port, self.username, self.password
        )
        self.client.connect()
        return self.client

    def publish(self, client, topic, value):
        """
        Publish a value to an MQTT topic, tracking consecutive errors.

        Args:
            client: Connected MQTTClient instance.
            topic (bytes): MQTT topic, e.g. ``b"room/humidity"``.
            value: Value to publish; converted to str before sending.

        Returns:
            bool: True on success, False after exceeding the error threshold.
        """
        print("start publishMqtt", 1)
        print(f"start publishMqtt topic={topic} value={value}", 1)

        try:
            result = client.publish(topic, str(value))
        except Exception as e:  # BUG-18 pattern fixed: typed except
            print(f"Failed to send message {value} to topic {topic}: {e}")
            self.errorcount += 1  # BUG-02 fixed: was bare errorcount
            if self.errorcount > 1500:  # 0,2s*5 * 5*60s
                # break the loop and reconnect
                self.connection_running = False
                return False
        else:
            print(f"Send `{value}` to topic `{topic}`")
            self.errorcount = 0  # BUG-02 fixed
            return True

    def reconnect_on_error(self):
        pass
        # TODO: reuse init to get a new connection
        # __init__()


def main():
    mqtt = MQTT()
    mqttclient = mqtt.connect()
    topicHumidity = b"debugroom/humidity"
    mqtt.publish(mqttclient, topicHumidity, 50)
    topicTemperature = b"debugroom/temperature"
    mqtt.publish(mqttclient, topicTemperature, 20)
    topicWater = b"water"
    mqtt.publish(mqttclient, topicWater, 100)


if __name__ == "__main__":
    sys.exit(main())
