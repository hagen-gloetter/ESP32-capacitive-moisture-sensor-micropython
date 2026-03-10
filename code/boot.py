# This file is executed on every boot (including wake-boot from deepsleep)
"""
boot.py — MicroPython boot script.

Executed before main.py on every power-on or reset.
Disables UART debug output, runs garbage collection to free flash memory.
WebREPL is disabled by default; uncomment to enable remote REPL access.
"""
import os
import time
import gc
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

