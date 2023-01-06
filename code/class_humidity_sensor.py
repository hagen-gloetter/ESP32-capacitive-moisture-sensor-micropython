import dht
from machine import Pin
import sys
import time


class HumiditySensor():
    """ Class to connect your ESP32 to a dht-Sensor

    """

    def __init__(self, pin=33):
        self.temperature = 0
        self.humidity = 0
        self.oldtemperature = 0
        self.oldhumidity = 0

        self.pin = pin
        self.sensor = dht.DHT11(Pin(self.pin))

    def get_humidity_and_temperature(self):
        self.sensor.measure()
        temperature = self.sensor.temperature()
        humidity = self.sensor.humidity()
        list = [temperature, humidity]
        return (list)

    def get_humidity(self):
        self.sensor.measure()
        humidity = self.sensor.humidity()
        return humidity

    def get_temperature(self):
        self.sensor.measure()
        temperature = self.sensor.temperature()
        return temperature

    def set_oldtemperature(self,old):
        self.oldtemperature=old
        
    def set_oldhumidity(self,old):
        self.oldhumidity=old

    def get_oldtemperature(self):
        return self.oldtemperature
        
    def get_oldhumidity(self):
        return self.oldhumidity



def main():
    sensor = HumiditySensor()
    (temperature, humidity) = sensor.get_humidity_and_temperature()
    print(f"temperature={temperature}, humidity={humidity}")


if __name__ == '__main__':
    sys.exit(main())

