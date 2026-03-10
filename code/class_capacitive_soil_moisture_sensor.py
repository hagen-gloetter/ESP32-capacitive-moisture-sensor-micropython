from machine import Pin, ADC
"""
class_capacitive_soil_moisture_sensor.py — Capacitive soil moisture sensor via ADC.

The raw 12-bit ADC value (0–4095) is mapped to an absolute moisture range
(0–2048) and then to a percentage (0–100 %).  Un-saturated soil reads low;
fully saturated / submerged sensor reads at the high end.

Usage::

    from class_capacitive_soil_moisture_sensor import MoistureSensor
    sensor = MoistureSensor(pin=32)
    print(sensor.get_moisture(), "%")

Hardware:
    - Capacitive soil moisture sensor AOUT → GPIO 32 (default, ADC1_CH4)
"""
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
        """Return the raw 12-bit ADC reading (0–4095)."""
        moisture = self.sensor.read()
#        moisture -= self.offset + self.offset
        return moisture

    def get_moisture_abs(self):
        """
        Return absolute moisture in the range 0–2048.

        The sensor output is inverted (dry → high ADC, wet → low ADC),
        so the value is reflected around 4095.
        """
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
        """
        Return soil moisture as an integer percentage (0–100).

        Returns:
            int: Moisture percentage derived from ``get_moisture_abs()``.
        """
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
