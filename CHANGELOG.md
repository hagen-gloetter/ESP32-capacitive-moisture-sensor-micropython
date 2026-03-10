# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

---

## [Session 1] — 2026-03-10

### Fixed

- **BUG-01** `class_mqtt.py:11` — Invalid class definition `class MQTT(pin=13):`.
  Python forbids keyword arguments in a class header; the file could not be imported at all.
  Changed to `class MQTT:`.

- **BUG-02** `class_mqtt.py:44,47` — `errorcount` used without `self.` prefix inside
  `publish()`.  Would raise `UnboundLocalError` on first publish failure.
  Changed to `self.errorcount`.

- **BUG-03** `class_mqtt.py:34` — `self.client_id` referenced in `connect()` but never
  assigned in `__init__`.  Would raise `AttributeError` on `connect()`.
  Added `client_id` constructor parameter; default `"mqtt-watermeter"`.

- **BUG-04** `main.py`, `main_mp.py` — `errorcount` and `running` used inside `publishMqtt`
  via `global` declarations but never initialised at module level.  Would raise `NameError`
  on the first publish error.  Added `errorcount = 0` and `running = True` at module level.

- **BUG-05** `main.py:95`, `main_mp.py:102` — `if debug == True:` compares a *function
  object* to `True` (always False).  In debug mode the production topic was always used
  instead of the debug topic.  Changed to `if debugmode:`.

- **BUG-06** `main.py:87`, `main_mp.py:87`, `class_mqtt.py:17` — `ujson.load(open(...))`
  left the file handle open indefinitely.  Changed to `with open(...) as f:` context
  managers throughout.

- **BUG-07** `class_wifi_connection.py:37` — Same unclosed file handle as BUG-06 for
  `secrets_wifi.json`.  Changed to context manager.

- **BUG-08** `main.py:139`, `main_mp.py:141` — `sensor_timer()` called `get_sensor_input()`
  without the required `publish_data` argument → `TypeError` whenever the sensor timer fired.
  Changed to `get_sensor_input("display_only")`.

- **BUG-09** `main.py:169`, `main_mp.py:162` — `"get_sensor_input called " + publish_data`
  raises `TypeError` when `publish_data` is not a `str` (e.g. Timer object in timer-callback
  path, or the initial `0` integer at module level).
  Changed to f-string: `f"get_sensor_input called {publish_data}"`.

- **BUG-10** `class_webserver.py:47` — In the `except` handler, `conn.send(...)` and
  `conn.close()` were called unconditionally.  If the exception occurred inside
  `websocket.accept()`, `conn` was never assigned → `UnboundLocalError`.
  Added `conn = None` before the `try` block and guarded the handler with
  `if conn is not None:`.

- **BUG-11** `class_webserver.py:14` — TCP socket created without `SO_REUSEADDR`.
  After a crash or reset, port 80 remained occupied for ~60 s → `OSError: [Errno 98]
  EADDRINUSE` on the next boot.
  Added `self.websocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)`.

- **BUG-12** `class_webserver.py:39-43` — HTTP status line, headers, and HTML body sent
  as `str` objects.  MicroPython sockets require `bytes`; sending `str` raises `TypeError`
  on MicroPython 1.18+.  Changed all header literals to `b"..."` with proper CRLF (`\r\n`)
  and added `.encode()` on the HTML body.

- **BUG-13** `class_webserver.py:36` — `float(level)` called on raw URL-parameter text
  without error handling.  An invalid URL parameter (e.g. `?wm=abc`) raised an unhandled
  `ValueError`.  Wrapped in `try/except ValueError`.

- **BUG-14** `class_ntp.py:18` — `ntptime.settime()` called without try/except.
  Any network error (timeout, DNS failure) during boot would crash the program.
  Wrapped in `try/except Exception`; failure is logged and `sync_time()` returns early,
  leaving the RTC at its current value.

- **BUG-15** `class_ntp.py:34` — DST "previous Sunday" formula `day - weekday + 1` is
  wrong for all weekdays (off by 1–7 days).
  MicroPython weekday encoding: 0 = Monday, 6 = Sunday.
  Correct formula: `previous_sunday = day - (weekday + 1) % 7`.
  Verification: Sunday (6) → `day - 0 = day` ✓; Monday (0) → `day - 1` ✓;
  Saturday (5) → `day - 6` ✓.

- **BUG-16** `class_humidity_sensor.py:32` — Bare `except:` clause swallowed all
  exceptions (including `KeyboardInterrupt`, `SystemExit`) silently.
  Changed to `except Exception as e:` with a diagnostic print.

- **BUG-17** `class_wifi_connection.py:38` — Same bare `except:` in `connect()`.
  Changed to `except Exception as e:`.

- **BUG-18** `main.py`, `main_mp.py` — Bare `except:` in `publishMqtt()`.
  Changed to `except Exception as e:` with error detail in the print.

- **BUG-19** `main.py:244` — `interval_update = 5*60` immediately overwritten by
  `interval_update = 30` on the next line (dead code) with a wrong comment ("5 min"
  for a 30-second value).  Removed the dead first assignment; fixed comments.

- **BUG-20** `main_mp.py` — `stop_all()` called `timer0.deinit()` unconditionally.
  `timer0` is only created when `timermode == True`; calling `stop_all()` with
  `timermode=False` raised `NameError`.  Guarded with `if timermode:`.

- **BUG-21** `class_wifi_connection.py` — WiFi connect timeout was 10 000 ms which is
  **longer** than the WDT timeout (8 000 ms).  During a reconnect attempt inside the
  main loop (where the WDT is active), the watchdog would fire before the WiFi timeout
  expired, causing an unwanted reset.  Reduced to 7 000 ms (< WDT timeout).

### Added

- **Phase 2 — WDT** `main.py` — Hardware watchdog enabled after all peripherals are
  initialised (`WDT(timeout=8000)`).  `wdt.feed()` added at the top of the main loop.
  WDT timeout (8 s) > max loop iteration + max reconnect delay (6 s).

- **Phase 2 — MQTT backoff** `main.py` — Initial MQTT `connect()` now retries with
  exponential backoff (1 s → 2 s → 4 s → 6 s cap via `MQTT_BACKOFF_MAX = 6`).
  `utime.sleep()` used (not blocking indefinitely) so WDT can be fed between retries
  (backoff values are all < WDT timeout).

- **Phase 2 — Non-blocking MQTT socket** `main.py` — `myMqttClient.sock.settimeout(0.5)`
  set immediately after connect so `check_msg()` calls do not block the main loop.

- **Phase 3 — Docstrings** — Module, class, and public-method docstrings added to all
  source files: `boot.py`, `class_mqtt.py`, `class_ntp.py`, `class_webserver.py`,
  `class_humidity_sensor.py`, `class_capacitive_soil_moisture_sensor.py`,
  `class_watermeter.py`, `class_oled_display.py`, `class_wifi_connection.py`, `main.py`.
