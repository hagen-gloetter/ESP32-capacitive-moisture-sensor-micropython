from machine import Pin
"""
class_watermeter.py — Reed-contact pulse counter for a magnetic water meter.

Reads a reed contact (normally open, closes when the meter's magnet wheel passes)
and counts pulses with a software Schmitt trigger to debounce.  The counter is
persisted to ``waterlevel.txt`` on the flash filesystem so values survive resets.

Each complete on→off→on transition counts as two increments of 2.5 L = 5 L/pulse,
matching one full wheel rotation on standard German household meters.

Usage::

    from class_watermeter import Watermeter
    wm = Watermeter(pin=13)
    # call every 200 ms to avoid missing pulses:
    count = wm.getWaterCount()  # litres (float)

Hardware:
    - Reed contact / dry relay between GPIO 13 (default) and GND
    - Internal pull-up enabled (``Pin.PULL_UP``)
"""
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
        """
        Load the persisted counter value from ``waterlevel.txt``.

        Returns:
            float: Counter value in litres, or 0.0 if the file does not exist.
        """
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
        """
        Overwrite the counter with an arbitrary value and persist to flash.

        Args:
            waterCounter (float): New counter value in litres.
        """
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
        """
        Poll the reed contact, apply Schmitt-trigger debounce, and return current count.

        Must be called at least every 200 ms (typically via a hardware timer) to
        avoid missing short pulses.

        Returns:
            float: Accumulated water volume in litres.
        """
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

