from machine import Pin, SoftI2C
"""
class_oled_display.py — SSD1306 I²C OLED display driver wrapper.

Manages a 128×64 px OLED display (SSD1306) connected via I²C.  The screen is
divided into six text lines (line height 10 px).  Each call to ``displayText``
updates one line and redraws the full display.

Usage::

    from class_oled_display import OledDisplay
    oled = OledDisplay()           # SCL=22, SDA=21 by default
    oled.displayText(0, "Hello")   # line 0
    oled.displayText(1, "World")   # line 1

Hardware:
    - OLED SCL → GPIO 22
    - OLED SDA → GPIO 21
    - Supply: 3.3 V / 5 V depending on module
"""
import ssd1306
from time import sleep
import sys
import time


class OledDisplay:
    """Class to connect your ESP32 to a OLED - Display"""

    def __init__(self, scl=22, sda=21, oled_width=128, oled_height=64):
        self.scl = Pin(scl)  # 22
        self.sda = Pin(sda)  # 21
        self.oled_width = oled_width  # 128
        self.oled_height = oled_height  # 64
        self.lineheight = 10
        self.textlines = ["Line0", "Line1", "Line2", "Line3", "Line4", "Line5"]
        #    def init_display(scl, sda):
        # ESP32 Pin assignment
        # i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
        i2c = SoftI2C(self.scl, self.sda)
        # ESP8266 Pin assignment
        # i2c = SoftI2C(scl=Pin(5), sda=Pin(4))
        self.oled = ssd1306.SSD1306_I2C(self.oled_width, self.oled_height, i2c)
        self.oled.text("init_display", 0, 0)
        self.oled.show()
        # return self.oled

    def displayText(self, line, text):
        """
        Update a single text line and redraw the full display.

        Args:
            line (int): Line index 0–5 (top to bottom, 10 px per line).
            text (str): Text to display on the given line.
        """
        self.textlines[line] = text
        self.oled.fill(0)
        for i in range(len(self.textlines)):
            self.oled.text(str(self.textlines[i]), 0, i * self.lineheight, 1)
        self.oled.show()


def main():
    oled = OledDisplay()
    oled.displayText(0, "Hallo 0")
    oled.displayText(1, "Hallo 1")
    oled.displayText(2, "Hallo 2")
    oled.displayText(3, "Hallo 3")
    oled.displayText(4, "Hallo 4")
    oled.displayText(5, "Hallo 5")


if __name__ == "__main__":
    sys.exit(main())


