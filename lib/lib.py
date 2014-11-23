__author__ = 'Sean Paley'
import re
from datetime import datetime

def parse_time(time_input):
    if not time_input:
        return None
    m = re.search("""(?P<hour>[0,1]?\d):?(?P<minute>\d{1,2})?\s*(?P<ampm>am|pm)?""", time_input, re.IGNORECASE)
    if m:
        hour = int(m.group("hour"))
        minute = m.group("minute")
        if not minute:
            minute = 0
        ampm = m.group("ampm")
        ampm = ampm.lower() if ampm else "pm"
        if ampm == "pm":
            hour += 12

        return datetime(2000, 1, 1, hour, int(minute))
    return None

def parse_phone(phone_input):
    if not phone_input:
        return None
    m = re.search("""^\D*1?(\d{3})\D*(\d{3})\D*(\d{4})\D*$""", phone_input)
    if m:
        return "+1%s%s%s" % (m.group(1), m.group(2), m.group(3))
    return None

def format_leave_time(leave_time):
    if not leave_time:
        return ""
    fmt = leave_time.strftime("%I:%M %p")
    if fmt.startswith("0"):
        fmt = fmt[1:]
    return fmt