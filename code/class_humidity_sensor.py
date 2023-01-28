# Written 10.2022 by Hagen@gloetter.de

import dht
from machine import Pin
import sys
import time


class HumiditySensor:
    """Class to connect your ESP32 to a dht-Sensor"""

    # Important!
    # if this is called TOO FAST the DHT returns a
    # OSError: [Errno 116] ETIMEDOUT
    # and stops your program execution.
    # to avoid this I use try/except
    # on error Ireturn the old values

    def __init__(self, pin=33):
        self.temperature = 0
        self.humidity = 0
        self.oldtemperature = 0
        self.oldhumidity = 0

        self.pin = pin
        self.sensor = dht.DHT11(Pin(self.pin))

    def get_temperature(self):
        self.oldtemperature = self.temperature
        try:
            self.sensor.measure()
            self.temperature = self.sensor.temperature()
        except:
            self.temperature = self.oldtemperature
        return self.temperature

    def get_humidity(self):
        self.oldhumidity = self.humidity
        try:
            self.sensor.measure()
            self.humidity = self.sensor.humidity()
        except:
            self.humidity = self.oldhumidity
        return self.humidity

    def get_humidity_and_temperature(self):
        temperature = self.get_temperature()
        humidity = self.get_humidity()
        list = [temperature, humidity]
        return list

    def set_oldtemperature(self, old):
        self.oldtemperature = old

    def set_oldhumidity(self, old):
        self.oldhumidity = old

    def get_oldtemperature(self):
        return self.oldtemperature

    def get_oldhumidity(self):
        return self.oldhumidity


def main():
    sensor = HumiditySensor()
    while True:
        (temperature, humidity) = sensor.get_humidity_and_temperature()
        print(f"temperature={temperature}, humidity={humidity}")


if __name__ == "__main__":
    sys.exit(main())
