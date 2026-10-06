from datetime import date, timedelta

# 12-character Apple serial, 2010-2021. Year character, then whether that
# character is the second half of the year. The same letters repeat in
# 2020. This program only runs on MacBook8,1, so a letter that also means
# a year outside 2014-2017 is not used.
YEAR = {
    "C": (2010, False),
    "D": (2010, True),
    "F": (2011, False),
    "G": (2011, True),
    "H": (2012, False),
    "J": (2012, True),
    "K": (2013, False),
    "L": (2013, True),
    "M": (2014, False),
    "N": (2014, True),
    "P": (2015, False),
    "Q": (2015, True),
    "R": (2016, False),
    "S": (2016, True),
    "T": (2017, False),
    "V": (2017, True),
    "W": (2018, False),
    "X": (2018, True),
    "Y": (2019, False),
    "Z": (2019, True),
}

# Week character within a half-year. Second half adds 26.
# Y is week 53, and only in the second half.
# Source: OpenCorePkg Utilities/macserial/FORMAT.md. Weeks are 7-day
# spans from January 1, not ISO weeks.
WEEK = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "C": 10,
    "D": 11,
    "F": 12,
    "G": 13,
    "H": 14,
    "J": 15,
    "K": 16,
    "L": 17,
    "M": 18,
    "N": 19,
    "P": 20,
    "Q": 21,
    "R": 22,
    "T": 23,
    "V": 24,
    "W": 25,
    "X": 26,
}


def manufacture_date(serial):
    serial = (serial or "").strip().upper()
    if len(serial) != 12 or serial[3] not in YEAR or not serial.isalnum():
        return None
    year, second = YEAR[serial[3]]
    if not 2014 <= year <= 2017:
        return None
    week = _week(serial[4], second)
    if week is None:
        return None
    built = date(year, 1, 1) + timedelta(days=(week - 1) * 7)
    if built > date(year, 12, 31) + timedelta(days=6):
        return None
    return built


def format_age(built, today):
    if built > today:
        return ""
    months = (today.year - built.year) * 12 + (today.month - built.month)
    if today.day < built.day:
        months -= 1
    if months < 0:
        return ""
    years, rem = divmod(months, 12)
    if years and rem:
        return f"{years} years, {rem} months"
    if years:
        return f"{years} years"
    return f"{rem} months"


def computer_line(built, today):
    age = format_age(built, today)
    if not age:
        return ""
    made = f"{built.day} {built.strftime('%B')} {built.year}"
    return f"Computer age  {age}    made {made}"


def computer_status(state):
    if state == "password":
        return "Computer age  needs a root password (press u)"
    if not state or state == "unknown":
        return "Computer age  unknown"
    return state


def _week(char, second):
    if second and char == "Y":
        return 53
    if char not in WEEK:
        return None
    return WEEK[char] + (26 if second else 0)
