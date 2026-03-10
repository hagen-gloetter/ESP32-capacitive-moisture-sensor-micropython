# NTP Klasse
"""
class_ntp.py — NTP time synchronisation with Central European Time (CET/CEST) offset.

Syncs the ESP32 RTC to UTC via an NTP server, then applies the correct CET (+1)
or CEST (+2, daylight-saving) offset so that subsequent RTC reads return local time.

Usage::

    import class_ntp, class_wifi_connection
    wifi = class_wifi_connection.WifiConnect()
    wifi.connect()
    ntp = class_ntp.NTPClock()
    ntp.sync_time(wifi)
    print(ntp.get_time())  # "HH:MM:SS"

Hardware:
    No dedicated pins — uses the built-in RTC and network stack.
"""

import ntptime
import utime
import machine


class NTPClock:
    """
    Manages NTP synchronisation and CET/CEST timezone offset for the ESP32 RTC.

    Notes:
        sync_time() must be called once after WiFi is connected.
        Timezone transitions are computed from calendar rules; sub-hour accuracy
        on DST-change days may be off by up to one hour (acceptable for display).
    """
    def __init__(self):
        self.timeout = 5 * 60  # 5 minutes timeout in seconds
        self.rtc = machine.RTC()

    def sync_time(self, wlan):
        """
        Wait for WiFi, fetch UTC time via NTP, apply CET/CEST offset, set RTC.

        Args:
            wlan: A WifiConnect instance (must expose ``isconnected() -> bool``).

        Notes:
            Resets the device if WiFi is not available within ``self.timeout`` seconds.
            Falls back to existing RTC time silently if the NTP request fails.
        """
        start_time = utime.time()
        while not wlan.isconnected():
            if utime.time() - start_time >= self.timeout:
                machine.reset()
            utime.sleep(1)
        try:
            ntptime.settime()  # BUG-14 fixed: was unguarded, can raise OSError
        except Exception as e:
            print(f"NTP sync failed: {e} — using RTC time")
            return
        year, month, day, hour, minute, second, weekday, yearday = utime.localtime()
        is_dst = self.is_dst()
        # Convert to CET time zone
        hour = (hour + 2) % 24 if is_dst else (hour + 1) % 24
        # Set RTC time
        self.rtc.datetime((year, month, day, weekday, hour, minute, second, 0))
        print(f"{year}, {month}, {day}, {weekday}, {hour}, {minute}, {second}")

    def is_dst(self):
        """
        Determine whether Central European Summer Time (CEST, UTC+2) is active.

        Returns:
            bool: True if DST (CEST) is in effect, False for standard CET.

        Notes:
            Uses the current UTC time from ``utime.localtime()``.
            DST is active from the last Sunday in March to the last Sunday in
            October, per EU rules.  The transition hour (2:00/3:00) is not
            checked — accuracy is ±1 h on the changeover days.
        """
        # Determine if DST is in effect
        year, month, day, hour, minute, second, weekday, yearday = utime.localtime()
        if month < 3 or month > 10:
            return False
        if month > 3 and month < 10:
            return True
        # BUG-15 fixed: correct formula for "most recent Sunday on or before today".
        # utime weekday: 0=Mon, 6=Sun
        # previous_sunday = day - (weekday + 1) % 7
        # Verification: Sun(6): day-0=day; Mon(0): day-1; Sat(5): day-6
        previous_sunday = day - (weekday + 1) % 7
        if month == 3:
            return previous_sunday >= 25
        if month == 10:
            return previous_sunday < 25

    def get_time(self):
        """
        Return the current local time as a formatted string.

        Returns:
            str: Local time in "HH:MM:SS" format read from the RTC.
        """
        year, month, day, weekday, hour, minute, second, subsecond = self.rtc.datetime()
        return "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
