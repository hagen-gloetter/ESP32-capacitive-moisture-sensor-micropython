import ujson
"""
class_wifi_connection.py — Multi-SSID WiFi connection manager.

Reads a list of known SSID/password pairs from ``secrets_wifi.json``, scans for
available networks, and connects to the first match.  Exposes a ``check_connection``
method for use in the main loop to detect and recover from dropped connections.

Usage::

    from class_wifi_connection import WifiConnect
    wifi = WifiConnect()
    status, ssid, ip = wifi.connect()
    # in main loop:
    status, ssid, ip = wifi.check_connection()

Secrets file (``secrets_wifi.json``)::

    {"MySSID": "passphrase", "BackupSSID": "otherpass"}
"""
import network
from network import WLAN
import machine
from machine import Timer
import sys
from time import sleep_ms
import utime  # Verwende utime f�r Zeitmessung in MicroPython


class WifiConnect:
    """Class to connect your ESP32 to local Wifi
    SSID and WiFi PW are read from file: secrets_wifi.json
    Usage:
    # Setup Wifi
    import class_wifi_connection
    global wifi
    wifi = class_wifi_connection.WifiConnect()
    (wifi_status, wifi_ssid, wifi_ip) = wifi.connect()
    # in a loop or timer
    list = wifi.check_connection()
    for item in list:
        print(item)
    # stop
        wifi.disconnect()
    """

    def __init__(self):
        self.wifi_ssid = "offline"
        self.wifi_pw = "hidden"
        self.wifi_ip = "offline"
        self.wifi_status = "offline"
        self.wifi = None

    def connect(self):
        print("connect wifi called")
        fn_secrets = "secrets_wifi.json"
        try:
            with open(fn_secrets) as f:  # BUG-07 fixed: use context manager
                wlan_json = ujson.load(f)
        except Exception as e:  # BUG-17 fixed: typed except
            print(f"!!!!!!!!!!!!!!!! ERROR !!!!!!!!!!!!!!!! File not found {fn_secrets}: {e}")
            return ("offline", "offline", "offline")
        else:
            print(f"connect wifi called with {fn_secrets}")
            # print (wlan_json)
            # print (type (wlan_json))
            # for key in wlan_json.keys():
            #    print (key)
            self.wifi = network.WLAN(network.STA_IF)
            self.wifi.active(True)
            self.wifi.disconnect()  # ensure we're disconnected
            nets = self.wifi.scan()
            # print ("NETS: ",nets)
            # print (type (nets))
            for ssid in wlan_json.keys():
                if ssid in str(nets):
                    print(f"++++++++ Network {ssid} found!")
                    pwd = wlan_json[ssid]
                    print("Trying to connect to SSID:", ssid)
                    (
                        self.wifi_status,
                        self.wifi_ssid,
                        self.wifi_ip,
                    ) = self.try_wifi_connect(ssid, pwd)
                    if self.wifi_status == "online":
                        break
            list = [self.wifi_status, self.wifi_ssid, self.wifi_ip]
            return list
            
            

    def try_wifi_connect(self, ssid=None, pwd=None):
        """
        Attempt to connect to a single SSID with a 10-second timeout.

        Args:
            ssid (str): Network SSID.  Defaults to last used SSID.
            pwd  (str): WPA passphrase.  Defaults to last used password.

        Returns:
            list: ``[status, ssid, ip]`` where status is ``"online"`` or ``"offline"``.
        """
        if ssid is None:
            ssid = self.wifi_ssid
            pwd = self.wifi_pw
        try:
            self.wifi.connect(ssid, pwd)
            timeout = 7000  # 7 s — must be < WDT timeout (8 s) so reconnect in the main loop does not trigger the WDT
            start_time = utime.ticks_ms()  # Millisekunden-Z�hler
            while not self.wifi.isconnected():
                if utime.ticks_diff(utime.ticks_ms(), start_time) > timeout:
                    print("Connection timeout reached")
                    break
                machine.idle()  # save power while waiting

            if self.wifi.isconnected():
                self.wifi_status = "online"
                self.wifi_ssid = ssid
                self.wifi_pw = pwd
                self.wifi_ip = self.wifi.ifconfig()[0]
                print("Connected to " + self.wifi_ssid)
                print(" with IP address: " + self.wifi_ip)
            else:
                raise Exception("Connection failed")

        except Exception as e:
            print(f"Failed to connect to any known network: {e}")
            self.wifi_status = "offline"
            self.wifi_ssid = "offline"
            self.wifi_ip = "offline"
            self.wifi.disconnect()  # ensure clean disconnect
        return [self.wifi_status, self.wifi_ssid, self.wifi_ip]

    def get_wifi_status(self):
        list = [self.wifi_status, self.wifi_ssid, self.wifi_ip]
        return list

    def isconnected(self):
        return self.wifi.isconnected()

    def check_connection(self):
        """
        Verify the WiFi link; reconnect if it is down.

        Returns:
            list: ``[status, ssid, ip]``.
        """
        print("check_connection called")
        if self.wifi_ssid == "offline":
            print("Attempting to connect to SSID:", self.wifi_ssid)
            self.connect()  # not connected at all
        elif not self.wifi.isconnected() or self.wifi_status == "offline":
            # no more  more connected
            self.wifi_status = "offline"
            print("Connection lost, trying to reconnect to SSID: ", self.wifi_ssid)
            (self.wifi_status, self.wifi_ssid, self.wifi_ip) = self.try_wifi_connect(
                self.wifi_ssid, self.wifi_pw
            )
        return [self.wifi_status, self.wifi_ssid, self.wifi_ip]

    def is_connected(self):
        print("is_connected called")
        (wifi_status, wifi_ssid, wifi_ip) = self.wifi.check_connection()
        list = [self.wifi_status, self.wifi_ssid, self.wifi_ip]
        return list

    def disconnect(self):
        """Disconnect from WiFi and reset cached state to \"offline\"."""
        print("disconnect called")
        self.wifi.disconnect()
        self.wifi_status = "offline"
        self.wifi_ssid = "offline"
        self.wifi_ip = "offline"

    def stop_all(self):
        print("stop_all called")
        self.disconnect()
        #self.wifi.disconnect()

def main():
    wifi = WifiConnect()  # Init the class
    (wifi_status, wifi_ssid, wifi_ip) = wifi.connect()  # connect to wifi
    i = 0
    while i == 0:
        list = wifi.check_connection()
        for item in list:
            print(item)
        sleep_ms(3000)
    wifi.disconnect()


if __name__ == "__main__":
    sys.exit(main())

