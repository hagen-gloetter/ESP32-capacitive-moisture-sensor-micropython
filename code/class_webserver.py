
import network
"""
class_webserver.py — Minimal HTTP webserver for displaying and updating the watermeter reading.

Runs in a dedicated MicroPython thread on port 80.  The single-page UI shows the
current water counter and allows manually setting the counter value via an HTML form
(useful after replacing the meter or resetting the ESP32).

Usage::

    from class_webserver import Webserver
    apache = Webserver()           # starts listener thread immediately
    # later ...
    apache.stop_webserver()        # sets run flag to False; thread exits after next accept()

Hardware:
    No dedicated pins — uses the active WiFi network interface (STA_IF).
"""
import socket
from machine import Pin
import class_watermeter
import time
import _thread
import re


class Webserver:
    """
    Minimal single-threaded HTTP server for watermeter management.

    Notes:
        Spawns a background thread on construction.  Shared state with the main
        loop is limited to reading ``gwaterCounter`` (class_watermeter global) which
        is safe under MicroPython’s cooperative threading model.
    """

    def __init__(self):
        print("Websocket init")
        self.websocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.websocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # BUG-11 fixed
        self.websocket.bind(("", 80))
        self.websocket.listen(5)
        time.sleep_ms(500)
        print("Websocket done")
        self.run_webserver = True
        _thread.start_new_thread(self.thread_webserver, (4, "webserver"))

    def thread_webserver(self, delay, name):
        print('Webserver gestartet.')
        c_watermeter = class_watermeter.Watermeter()
        while self.run_webserver == True:
            conn = None  # BUG-10 fixed: guard against use before assignment
            try:
                conn, addr = self.websocket.accept()
                print('Verbunden mit %s' % str(addr))
                request = conn.recv(1024)
                
                request = str(request)
                #print('Anfrage: ', request)
                if "wm=" in request:
                    level = request[request.find("wm=")+3:].split("&")[0].split(" ")[0]
                    print("MANUAL Waterlevel set =" + level)
                    try:  # BUG-13 fixed: protect float() from invalid user input
                        c_watermeter.setWaterCount(float(level))
                    except ValueError:
                        print(f"Invalid waterlevel value: {level!r}")
                level = str(c_watermeter.readWaterFile())
                response = self.html_code(level)
                conn.send(b"HTTP/1.1 200 OK\r\n")  # BUG-12 fixed: bytes + CRLF
                conn.send(b"Content-Type: text/html\r\n")
                conn.send(b"Connection: close\r\n\r\n")
                conn.sendall(response.encode())  # BUG-12 fixed: encode HTML
                conn.close()
            except Exception as e:
                if conn is not None:  # BUG-10 fixed: only use conn if it was assigned
                    conn.send(b"HTTP/1.1 500 Internal Server Error\r\n")  # BUG-12 fixed
                    conn.send(b"Content-Type: text/html\r\n")
                    conn.send(b"Connection: close\r\n\r\n")
                    response = "<h1>Failed: </h1>" + str(e)
                    conn.sendall(response.encode())  # BUG-12 fixed
                    conn.close()

    def stop_webserver(self):
        """Signal the webserver thread to stop after its current request."""
        self.run_webserver = False

    def html_code(self, level):
        html = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta http-equiv="x-ua-compatible" content="ie=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Watermeter reading</title>
        <!--<link rel="stylesheet" href="css/main.css" />
        <link rel="icon" href="images/favicon.png" />-->
    </head>
    <body>
        <form method=POST>
            <div class="form-group">
                <label>Watermeter</label> <input type="text" name="wm" value="'''+level+'''">
            </div>
            <div class="form-group">
                <input type="submit" class="btn btn-primary" name="button_save" value="Write Data to ESP">
            </div>
        </form>
        <!--<p><a href="/?LED=ON"><button>Einschalten</button></a></p>
        <p><a href="/?LED=OFF"><button>Ausschalten</button></a></p>-->
    </body>
</html>

'''
        return html
