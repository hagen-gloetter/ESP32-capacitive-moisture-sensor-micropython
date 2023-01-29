from machine import Pin
import time
import sys

debuglevel = 0


def debug(msg, level):
    global debuglevel
    if level <= debuglevel:
        print(msg)


class Watermeter:
    """Class to read a german Watermeter with a magnetic wheel
    every wheel-spin is a magnetic impulse
    this needs to be done very quick to not miss a impulse
    recommendation is 200ms
    Usage:
    # Setup
    watermeter = Watermeter()
    # in a loop or timer every 200ms
    waterlevel = watermeter.getWaterCounter()
    """

    def __init__(self, pin=13):
        self.pin = pin
        self.reedcontact = Pin(self.pin, Pin.IN, Pin.PULL_UP)
        self.waterLevelFn = "waterlevel.txt"
        self.debounceCounter = 0
        self.waterCounter = self.readWaterFile()
        self.oldwatercount = 0

    def readWaterFile(self):
        try:
            with open(self.waterLevelFn, "r") as f:
                self.waterCounter = float(f.readline().rstrip())
                f.close()
        except Exception as e:
            print(f"Failed to open {self.waterLevelFn}")
            self.waterCounter = 0
            self.setWaterCount(0)
        return self.waterCounter

    def setWaterCount(self, waterCounter):
        debug(f"setWaterCount {self.waterCounter}", 2)
        self.waterCounter = waterCounter
        with open(self.waterLevelFn, "w") as f:
            f.write("{0:0.1f}".format(self.waterCounter))
            f.close()
        # return water

    def increaseWaterCounter(self):
        debug(f"increaseWaterCounter {self.waterCounter}", 2)
        self.waterCounter += 2.5
        self.setWaterCount(self.waterCounter)
        return self.waterCounter

    def getWaterCount(self):
        debug("getWaterCounter: " + str(self.waterCounter), 2)
        # do a schmitt trigger to avoid bounce readings
        self.oldwatercount = self.waterCounter
        if self.reedcontact.value() == 0 and self.debounceCounter < 10:
            self.debounceCounter += 1
            if self.debounceCounter == 10:
                self.waterCounter = self.increaseWaterCounter()
        elif self.reedcontact.value() == 1 and self.debounceCounter > 0:
            self.debounceCounter -= 1
            if self.debounceCounter == 0:
                self.waterCounter = self.increaseWaterCounter()
        # if (self.oldwatercount != self.waterCounter):
        #   notify on change
        return self.waterCounter

    def getoldWaterCount(self):
        return self.oldwatercount

def main():
    watermeter = Watermeter()
    while True:
        waterlevel = watermeter.getWaterCount()
        time.sleep_ms(200)


if __name__ == "__main__":
    sys.exit(main())

