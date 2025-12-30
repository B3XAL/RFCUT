# =========================
# CONFIG
# =========================

import base64
import sys
from icu import Collator, Locale
from base64 import b64encode
from urllib.parse import quote
import time
import re
import signal
import random
import string
import idna
from utils.clipboard import copy

def clean_exit(signum=None, frame=None):
    print("\n\n\033[91m[ EXIT ]\033[0m Operation cancelled by user.\n")
    sys.exit(0)

signal.signal(signal.SIGINT, clean_exit)

CHARSETS = ["utf-8", "iso-8859-1", "utf-7", "x"]
ENCODINGS = ["q", "b"]

CHARS = list(string.ascii_letters)
WHITESPACE = [" ", "\t", "\r", "\n"]

collator = Collator.createInstance(Locale('en_US'))
collator.setStrength(collator.PRIMARY)  # Ignore case and accents
unicode_max = 0x10FFFF
URLENCODE = 0

PUNCTUATION = {
    "NONE": b"",
    ">":    b"\x3e",
    ",": b"\x2c",
    "/": b"\x2f",
    "//": b"\x2f\x2f",
    "\"": b"\x22",
    "\\": b"\x5c",
    ";":  b"\x3b",
    "SPACE":b"\x20",
}

CONTROL_CHARS = {
    "NONE": b"",
    "NULL": b"\x00",
    "SOH":  b"\x01",
    "STX":  b"\x02",
    "ETX":  b"\x03",
    "EOT":  b"\x04",
    "ENQ":  b"\x05",
    "ACK":  b"\x06",
    "BEL":  b"\x07",
    "BS":   b"\x08",
    "TAB":  b"\x09",
    "LF":   b"\x0A",
    "VT":   b"\x0B",
    "FF":   b"\x0C",
    "CR":   b"\x0D",
    "SO":   b"\x0E",
    "SI":   b"\x0F",
    "DLE":  b"\x10",
    "DC1":  b"\x11",
    "DC2":  b"\x12",
    "DC3":  b"\x13",
    "DC4":  b"\x14",
    "NAK":  b"\x15",
    "SYN":  b"\x16",
    "ETB":  b"\x17",
    "CAN":  b"\x18",
    "EM":   b"\x19",
    "SUB":  b"\x1A",
    "ESC":  b"\x1B",
    "FS":   b"\x1C",
    "GS":   b"\x1D",
    "RS":   b"\x1E",
    "US":   b"\x1F",
    "SPACE":b"\x20",

}

SPECIAL_SEQUENCES = {
    "CRLF": b"\x0D\x0A",
    "CRLF_TAB": b"\x0D\x0A\x09",
    "CRLF_SP":  b"\x0D\x0A\x20",
}
