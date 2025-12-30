# =========================
# ENCODERS
# =========================

import base64
from utils.config import *


def q_encode_force(data: bytes) -> str:
    """
    RFC 2047 Q-encoding
    """
    return "".join(f"={b:02X}" for b in data)

def q_encode_partial(raw: bytes, specials: set[int]) -> str:
    out = []
    for b in raw:
        if b in specials:
            out.append(f"={b:02X}")
        else:
            out.append(chr(b))
    return "".join(out)

def b_encode(data: bytes) -> str:
    """
    RFC 2045 Base64 with padding
    """
    return base64.b64encode(data).decode("ascii")


def encode_imap_utf7_full_from_bytes(raw: bytes) -> bytes:
    """
    FULL IMAP UTF-7 over the ENTIRE payload
    bytes -> latin-1 -> UTF-16BE -> Base64 modified -> &...-
    """
    text = raw.decode("latin-1")
    utf16 = text.encode("utf-16-be")
    b64 = base64.b64encode(utf16).decode("ascii")
    b64 = b64.replace("/", ",").rstrip("=")
    return f"&{b64}-".encode("ascii")

def detect_specials(raw: bytes) -> set[int]:
    specials = set()

    # 1) Control y no-ASCII
    for b in raw:
        if b < 0x20 or b >= 0x7F:
            specials.add(b)

    # 2) User-selected
    for v in PUNCTUATION.values():
        specials |= set(v)

    # 3) Control chars selected
    for v in CONTROL_CHARS.values():
        specials |= set(v)

    # 4) Special sequences
    for v in SPECIAL_SEQUENCES.values():
        specials |= set(v)

    # 5) Semantic separators within the user's text
    for b in b".@:-_":
        specials.add(b)

    return specials

def utf7_encode_partial(raw: bytes, specials: set[int]) -> bytes:
    out = bytearray()
    for b in raw:
        if b in specials:
            t = bytes([b]).decode("latin-1")
            u = t.encode("utf-16-be")
            b64 = base64.b64encode(u).decode().replace("/", ",").rstrip("=")
            out.extend(f"&{b64}-".encode())
        else:
            out.append(b)
    return bytes(out)

def encode_payload(raw: bytes, charset: str, encoding: str):
    """
    List of encoded-words
    """
    results = []

    # =========================
    # CHARSET PHASE
    # =========================

    if charset == "utf-7":
        data = encode_imap_utf7_full_from_bytes(raw)
    else:
        data = raw

    # =========================
    # ENCODING PHASE
    # =========================

    if encoding == "b":
        encoded = b_encode(data)
        results.append(f"=?{charset}?b?{encoded}?=")

    elif encoding == "q":

        if charset == "utf-7":
            # Variant A: UTF-7 without forced Q
            results.append(
                f"=?utf-7?q?{data.decode('ascii', 'ignore')}?="
            )

            # Variant B: only escaped '&'
            escaped = data.replace(b"&", b"=26")
            results.append(
                f"=?utf-7?q?{escaped.decode('ascii', 'ignore')}?="
            )

        else:
            q = q_encode_force(data)
            results.append(f"=?{charset}?q?{q}?=")

    else:
        raise ValueError("\033[91m[ ERROR ] Encoding inválido\033[0m")

    # =========================
    # PARTIAL VARIATIONS
    # =========================

    specials = detect_specials(raw)

    if specials:

        # --- Partial Q in any charset ---
        partial_q = q_encode_partial(raw, specials)
        results.append(f"=?{charset}?q?{partial_q}?=")

        # --- Partial UTF-7 ---
        utf7_partial = utf7_encode_partial(raw, specials)
        results.append(f"=?utf-7?q?{utf7_partial.decode('ascii','ignore')}?=")

        # ---  Partial UTF-7 + Q only on '&' ---
        q_on_amp = q_encode_partial(utf7_partial, {ord('&')})
        results.append(f"=?utf-7?q?{q_on_amp}?=")


    return results

