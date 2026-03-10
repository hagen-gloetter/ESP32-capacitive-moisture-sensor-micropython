# ESP32 Capacitive Moisture Sensor — MicroPython

**[Deutsch](#deutsch) | [English](#english)**

---

<a name="deutsch"></a>
## Deutsch

### Projektbeschreibung

Dieses Projekt betreibt einen ESP32 als autonomen Sensor-Node, der folgende Werte
erfasst und per MQTT an einen Broker (z. B. ioBroker, Home Assistant, Mosquitto) überträgt:

* **Bodenfeuchte** (kapazitiver Sensor, GPIO 32, 0–100 %)
* **Temperatur & Relative Luftfeuchtigkeit** (DHT11, GPIO 33)
* **Wasserstand-Zähler** (Reed-Kontakt am Hauswasserzähler, GPIO 13)

Ein SSD1306 OLED-Display (128×64 px, I²C) zeigt alle Werte im Live-Betrieb an.
Ein eingebetteter HTTP-Server auf Port 80 ermöglicht das manuelle Setzen des
Wasserzähl-Startwerts über den Browser.

---

### Hardware

| Komponente | Board-Pin (GPIO) | Anmerkung |
|---|---|---|
| OLED SCL | GPIO 22 | SoftI²C |
| OLED SDA | GPIO 21 | SoftI²C |
| DHT11 DATA | GPIO 33 | 10 kΩ Pull-up empfohlen |
| Moisture AOUT | GPIO 32 | ADC1, keine WiFi-Nutzung gleichzeitig |
| Reed-Kontakt | GPIO 13 | Interner Pull-up aktiv, anderes Ende → GND |

**Getestetes Board:** ESP32 DevKitC (240 MHz, 4 MB Flash)

---

### Software / Abhängigkeiten

| Paket | Quelle |
|---|---|
| MicroPython ≥ 1.20 | [micropython.org](https://micropython.org/download/esp32/) |
| `umqtt.robust` | `mpremote mip install umqtt.robust` |
| `umqtt.simple` | `mpremote mip install umqtt.simple` |
| `ssd1306.py` | im Repository enthalten |

---

### Konfiguration

#### Laufzeit-Konstanten in `main.py`

| Konstante | Standardwert | Bedeutung |
|---|---|---|
| `debugmode` | `False` | `True` → MQTT-Prefix = `debugroom` statt `room.txt` |
| `timermode` | `False` | `True` → Sensoren per Timer, nicht im Haupt-Loop |
| `MQTT_BACKOFF_MAX` | `6` | Max. Reconnect-Pause in Sekunden (< WDT-Timeout 8 s!) |
| `interval` | `1` | Haupt-Loop-Takt in Sekunden |
| `interval_update` | `30` | Änderungs-Publish-Intervall in Sekunden |
| `interval_force` | `600` | Erzwungener Publish alle 10 Minuten |

#### Secrets-Dateien (auf dem ESP32-Flash)

**`secrets_wifi.json`**
```json
{
  "MeinSSID": "wlan-passwort",
  "BackupSSID": "backup-passwort"
}
```

**`secrets_mqtt.json`**
```json
{
  "secretHost": "broker.fritz.box",
  "secretPort": 1883,
  "secretUser": "mqtt-user",
  "secretPass": "mqtt-pass"
}
```

**`room.txt`** — Ein Wort, kein Zeilenumbruch, z. B.:
```
wohnzimmer
```

---

### MQTT-Topics

| Topic | Inhalt | Datentyp |
|---|---|---|
| `<room>/humidity` | Relative Luftfeuchtigkeit | int (%) |
| `<room>/temperature` | Temperatur | int (°C) |
| `<room>/moisture` | Bodenfeuchte | int (%) |
| `watermeter/value` | Wassermenge kumuliert | float (L) |

`<room>` wird aus `room.txt` gelesen. Bei `debugmode = True` wird `debugroom` verwendet.

---

### Webserver (Port 80)

Der eingebettete HTTP-Server startet automatisch. Öffne `http://<ESP32-IP>/` im Browser
um den aktuellen Wasserzählerstand zu sehen und manuell zu setzen.

---

### WebREPL (optional)

```python
# In boot.py (Zeilen auskommentieren):
import webrepl
webrepl.start()
```

Erstmaliges Einrichten:
```bash
mpremote connect /dev/ttyUSB0 repl
# In der REPL:
import webrepl_setup
```

---

### Dateistruktur

```
code/
├── boot.py                                — Startet vor main.py, deaktiviert UART-Debug
├── main.py                                — Produktions-Einstiegspunkt (dieser Node)
├── main_mp.py                             — Alternative ohne Webserver (Debug/Backup)
├── class_capacitive_soil_moisture_sensor.py — ADC-Bodenfeuchte-Sensor
├── class_humidity_sensor.py               — DHT11 Temperatur & Luftfeuchtigkeit
├── class_mqtt.py                          — MQTT-Hilfsklasse (Prototype, nicht in main.py geladen)
├── class_ntp.py                           — NTP-Sync mit CET/CEST-Offset
├── class_oled_display.py                  — SSD1306 OLED-Display-Wrapper
├── class_watermeter.py                    — Reed-Kontakt-Impulszähler (persistiert)
├── class_webserver.py                     — Eingebetteter HTTP-Server (Thread)
├── class_wifi_connection.py               — Multi-SSID WiFi-Verbindungsmanager
└── ssd1306.py                             — Drittanbieter OLED-Treiber
```

---

### Flash / Deployment

```bash
# 1. MicroPython flashen (einmalig)
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin

# 2. Dateien übertragen
mpremote connect /dev/ttyUSB0 cp secrets_wifi.json :
mpremote connect /dev/ttyUSB0 cp secrets_mqtt.json :
mpremote connect /dev/ttyUSB0 cp room.txt :
mpremote connect /dev/ttyUSB0 cp code/ssd1306.py :
mpremote connect /dev/ttyUSB0 cp code/class_*.py :
mpremote connect /dev/ttyUSB0 cp code/boot.py :
mpremote connect /dev/ttyUSB0 cp code/main.py :

# 3. umqtt installieren
mpremote connect /dev/ttyUSB0 mip install umqtt.robust
```

---

### Bekannte Einschränkungen

* Reed-Kontakt (Wasserzähler): Der Sensor muss alle 200 ms abgerufen werden. Bei sehr
  langsamen Zählern und hoher CPU-Last können Pulse verloren gehen.
* DHT11-Auflösung: ±2 °C / ±5 % RH; für Präzisionsanwendungen DHT22 verwenden.
* Bodenfeuchte: Kalibrierung (Trocken/Nass-Referenz) ist nicht implementiert.
* MQTT-Topics: Slash-Format (`room/value`) – kompatibel mit Mosquitto, EMQX, ioBroker.
* Zeitzone: CET/CEST (UTC+1/+2). Auf der DST-Umschaltstunde (2:00/3:00 Uhr) kann die
  angezeigte Zeit um ±1 Stunde abweichen.

---

### Changelog

Siehe [CHANGELOG.md](CHANGELOG.md).

### Lizenz

Siehe [LICENSE](LICENSE).

---
---

<a name="english"></a>
## English

### Project Description

This project runs an ESP32 as an autonomous sensor node that measures and publishes
the following values via MQTT (compatible with ioBroker, Home Assistant, Mosquitto, EMQX):

* **Soil moisture** (capacitive sensor, GPIO 32, 0–100 %)
* **Temperature & relative humidity** (DHT11, GPIO 33)
* **Water meter counter** (reed contact on household water meter, GPIO 13)

An SSD1306 OLED display (128×64 px, I²C) shows all values live.
A built-in HTTP web server on port 80 allows manually setting the water-meter
start value from a browser.

---

### Hardware

| Component | Board pin (GPIO) | Notes |
|---|---|---|
| OLED SCL | GPIO 22 | SoftI²C |
| OLED SDA | GPIO 21 | SoftI²C |
| DHT11 DATA | GPIO 33 | 10 kΩ pull-up recommended |
| Moisture AOUT | GPIO 32 | ADC1 — do not use WiFi simultaneously |
| Reed contact | GPIO 13 | Internal pull-up enabled; other end → GND |

**Tested board:** ESP32 DevKitC (240 MHz, 4 MB flash)

---

### Software / Dependencies

| Package | Source |
|---|---|
| MicroPython ≥ 1.20 | [micropython.org](https://micropython.org/download/esp32/) |
| `umqtt.robust` | `mpremote mip install umqtt.robust` |
| `umqtt.simple` | `mpremote mip install umqtt.simple` |
| `ssd1306.py` | included in this repository |

---

### Configuration

#### Runtime constants in `main.py`

| Constant | Default | Description |
|---|---|---|
| `debugmode` | `False` | `True` → MQTT prefix = `debugroom` instead of `room.txt` |
| `timermode` | `False` | `True` → sensors polled via hardware timer |
| `MQTT_BACKOFF_MAX` | `6` | Maximum reconnect delay in seconds (must be < WDT timeout 8 s) |
| `interval` | `1` | Main loop tick in seconds |
| `interval_update` | `30` | Change-triggered publish interval in seconds |
| `interval_force` | `600` | Force-publish all values every 10 minutes |

#### Secrets files (stored on ESP32 flash)

**`secrets_wifi.json`**
```json
{
  "MySSID": "wifi-password",
  "BackupSSID": "backup-password"
}
```

**`secrets_mqtt.json`**
```json
{
  "secretHost": "broker.local",
  "secretPort": 1883,
  "secretUser": "mqtt-user",
  "secretPass": "mqtt-pass"
}
```

**`room.txt`** — single word, no line break, e.g.:
```
livingroom
```

---

### MQTT Topics

| Topic | Content | Data type |
|---|---|---|
| `<room>/humidity` | Relative humidity | int (%) |
| `<room>/temperature` | Temperature | int (°C) |
| `<room>/moisture` | Soil moisture | int (%) |
| `watermeter/value` | Accumulated water volume | float (L) |

`<room>` is read from `room.txt`. When `debugmode = True`, `debugroom` is used.

---

### Web Server (port 80)

The built-in HTTP server starts automatically. Open `http://<ESP32-IP>/` in a browser
to view and manually update the water-meter counter.

---

### WebREPL (optional)

```python
# In boot.py (uncomment the lines):
import webrepl
webrepl.start()
```

First-time setup:
```bash
mpremote connect /dev/ttyUSB0 repl
# In the REPL:
import webrepl_setup
```

---

### File Structure

```
code/
├── boot.py                                — Runs before main.py; disables UART debug
├── main.py                                — Production entry point
├── main_mp.py                             — Alternative without web server (debug/backup)
├── class_capacitive_soil_moisture_sensor.py — ADC soil moisture sensor
├── class_humidity_sensor.py               — DHT11 temperature & humidity
├── class_mqtt.py                          — MQTT helper class (prototype, not loaded by main.py)
├── class_ntp.py                           — NTP sync with CET/CEST timezone offset
├── class_oled_display.py                  — SSD1306 OLED wrapper
├── class_watermeter.py                    — Reed contact pulse counter (persistent)
├── class_webserver.py                     — Embedded HTTP server (separate thread)
├── class_wifi_connection.py               — Multi-SSID WiFi connection manager
└── ssd1306.py                             — Third-party SSD1306 driver
```

---

### Flash / Deployment

```bash
# 1. Flash MicroPython (once)
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin

# 2. Upload files
mpremote connect /dev/ttyUSB0 cp secrets_wifi.json :
mpremote connect /dev/ttyUSB0 cp secrets_mqtt.json :
mpremote connect /dev/ttyUSB0 cp room.txt :
mpremote connect /dev/ttyUSB0 cp code/ssd1306.py :
mpremote connect /dev/ttyUSB0 cp code/class_*.py :
mpremote connect /dev/ttyUSB0 cp code/boot.py :
mpremote connect /dev/ttyUSB0 cp code/main.py :

# 3. Install umqtt
mpremote connect /dev/ttyUSB0 mip install umqtt.robust
```

---

### Known Limitations

* Reed contact (water meter): must be polled every 200 ms. Under heavy CPU load, pulses
  may be missed.
* DHT11 accuracy: ±2 °C / ±5 % RH. Use DHT22 for precision applications.
* Soil moisture: wet/dry calibration is not implemented; percentage is derived from a
  fixed ADC range.
* MQTT topics: slash format (`room/value`) — compatible with Mosquitto, EMQX, ioBroker.
* Timezone: CET/CEST (UTC+1/+2). On DST changeover hour the displayed time may be off
  by ±1 hour.

---

### Changelog

See [CHANGELOG.md](CHANGELOG.md).

### License

See [LICENSE](LICENSE).

