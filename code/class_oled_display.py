from machine import Pin, SoftI2C
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
        self.textlines = ["Line1", "Line2", "Line3", "Line4", "Line5", "Line6"]
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
