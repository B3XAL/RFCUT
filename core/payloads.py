# =========================
# PAYLOAD BUILDERS
# =========================

from core.encoders import *
from utils.config import *


def build_payload(base: str, punct: bytes | None, control: bytes | None) -> bytes:
    raw = base.encode("latin-1")

    if punct is not None:
        raw += punct

    if control is not None:
        raw += control

    return raw

def generate_all(raw: bytes):
    """
    Apply all charsets + encoding to the SAME payload
    """
    results = []
    for cs in CHARSETS:
        for enc in ENCODINGS:
            results.extend(encode_payload(raw, cs, enc))
    return results
