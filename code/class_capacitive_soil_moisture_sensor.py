from machine import Pin, ADC
import sys
import time


class MoistureSensor():
    """ Class to connect your ESP32 to a capacitive soil moisture sensor

    """

    def __init__(self, pin=32):
        self.moisture = 0
        self.pin = pin
        self.sensor = ADC(Pin(pin))
        self.sensor.read()
        # values from 2048 - 4095
        self.offset = 2048
        self.oldmoisture=0

    def get_moisture_raw(self):
        moisture = self.sensor.read()
#        moisture -= self.offset + self.offset
        return moisture

    def get_moisture_abs(self):
        moisture = self.sensor.read()
#        moisture -= self.offset + self.offset
        moisture = moisture - 4095
        moisture *= -1
        if moisture < 0:
            moisture = 0
        if moisture > 2048:
            moisture = 2048
        return moisture

    def get_moisture(self):
        moisture = self.get_moisture_abs()
        # values from 0 - 2048
        percent = (moisture)/(2048*100)*100
        percent = int(percent*100)
        return percent

    def get_oldmoisture(self):
        return self.oldmoisture
    
    def set_oldmoisture(self,old):
        self.oldmoisture=old
        

def main():
    sensor = MoistureSensor()
    while True:
        raw = sensor.get_moisture_raw()
        percent = sensor.get_moisture()
        moisture = sensor.get_moisture_abs()

        print(f"raw={raw} moisture={moisture} percent={percent} ")
        time.sleep(1)


if __name__ == '__main__':
    sys.exit(main())
