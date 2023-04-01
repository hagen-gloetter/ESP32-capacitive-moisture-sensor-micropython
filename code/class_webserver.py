
import network
import socket
from machine import Pin

class Webserver:

    def __init__(self, led_pin):
        self.led_pin = led_pin
        self.led = Pin(self.led_pin, Pin.OUT)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.s.bind(('', 80))
        self.s.listen(5)
        print('Webserver gestartet.')
        while True:
            conn, addr = self.s.accept()
            print('Verbunden mit %s' % str(addr))
            request = conn.recv(1024)
            request = str(request)
            print('Anfrage: ', request)
            led_on = request.find('/?LED=ON')
            led_off = request.find('/?LED=OFF')
            if led_on == 6:
                print('LED an.')
                self.led.value(1)
            if led_off == 6:
                print('LED aus.')
                self.led.value(0)
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
            response += '<html><body><h1>ESP32-Webseite</h1>'
            response += '<p><a href="/?LED=ON"><button>Einschalten</button></a></p>'
            response += '<p><a href="/?LED=OFF"><button>Ausschalten</button></a></p>'
            response += '</body></html>\r\n'
            conn.send(response.encode())
            conn.close()
