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
    global gwaterCounter

    def __init__(self, pin=13):
        global gwaterCounter
        self.pin = pin
        self.reedcontact = Pin(self.pin, Pin.IN, Pin.PULL_UP)
        self.waterLevelFn = "waterlevel.txt"
        self.debounceCounter = 0
        self.oldwatercount = 0
        gwaterCounter = self.readWaterFile()

    def readWaterFile(self):
        global gwaterCounter
        try:
            with open(self.waterLevelFn, "r") as f:
                gwaterCounter = float(f.readline().rstrip())
                f.close()
        except Exception as e:
            print(f"Failed to open {self.waterLevelFn}")
            gwaterCounter = 0
            self.setWaterCount(0)
        return gwaterCounter

    def setWaterCount(self, waterCounter):
        global gwaterCounter
        debug(f"setWaterCount {waterCounter}", 2)
        gwaterCounter = waterCounter
        with open(self.waterLevelFn, "w") as f:
            f.write("{0:0.1f}".format(gwaterCounter))
            print(f"setWaterCount WRITE {gwaterCounter}")
            f.close()
            
        # return water

    def increaseWaterCounter(self):
        global gwaterCounter
        debug(f"increaseWaterCounter {gwaterCounter}", 2)
        gwaterCounter += 2.5
        self.setWaterCount(gwaterCounter)
        return gwaterCounter

    def getWaterCount(self):
        global gwaterCounter
        debug("getWaterCounter: " + str(gwaterCounter), 2)
        # do a schmitt trigger to avoid bounce readings
        self.oldwatercount = gwaterCounter
        if self.reedcontact.value() == 0 and self.debounceCounter < 10:
            self.debounceCounter += 1
            if self.debounceCounter == 10:
                gwaterCounter = self.increaseWaterCounter()
        elif self.reedcontact.value() == 1 and self.debounceCounter > 0:
            self.debounceCounter -= 1
            if self.debounceCounter == 0:
                gwaterCounter = self.increaseWaterCounter()
        # if (self.oldwatercount != gwaterCounter):
        #   notify on change
        return gwaterCounter

    def getoldWaterCount(self):
        return self.oldwatercount

def main():
    watermeter = Watermeter()
    while True:
        waterlevel = watermeter.getWaterCount()
        time.sleep_ms(200)


if __name__ == "__main__":
    sys.exit(main())

