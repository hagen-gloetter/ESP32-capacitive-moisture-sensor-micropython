
import network
import socket
from machine import Pin
import class_watermeter
import time
import _thread
import re


class Webserver:

    def __init__(self):
        print("Websocket init")
        self.websocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
            try:
                conn, addr = self.websocket.accept()
                print('Verbunden mit %s' % str(addr))
                request = conn.recv(1024)
                
                request = str(request)
                #print('Anfrage: ', request)
                if "wm=" in request:
                    level=request[request.find("wm=")+3:].split("&")[0].split (" ")[0]
                    print("MANUAL Waterlevel set ="+ level)
                    c_watermeter.setWaterCount(float(level))
                    # time.sleep(1)
                level = str(c_watermeter.readWaterFile())
                response = self.html_code(level)
                conn.send("HTTP/1.1 200 OK\n")
                conn.send("Content-Type: text/html\n")
                conn.send("Connection: close\n\n")
                conn.sendall(response)
                conn.close()
            except Exception as e:
                conn.send("HTTP/1.1 200 OK\n")
                conn.send("Content-Type: text/html\n")
                conn.send("Connection: close\n\n")
                response = "<h1>'Failed: </h1>" + str(e)
                conn.sendall(response)
                conn.close()

    def stop_webserver(self):
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
