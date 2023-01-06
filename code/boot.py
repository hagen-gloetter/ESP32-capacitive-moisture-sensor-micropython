# This file is executed on every boot (including wake-boot from deepsleep)
import get_wifi_connection
import machine
import os
import time
import gc
from machine import Pin
import esp
esp.osdebug(None)
# esp.osdebug(None)
#import webrepl
print("boot.py")

# webrepl.start()
#print ("boot.py done")


#print("boot.py get_wifi_connection")
#(wifistatus, wifinetwork, ipaddress) = get_wifi_connection.connect_wifi()

print("boot.py done")
