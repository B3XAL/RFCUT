import base64
import sys
from icu import Collator, Locale
from base64 import b64encode
from urllib.parse import quote
import pyperclip
import time
import re

try:
    import pyperclip
    CLIPBOARD = True
except ImportError:
    CLIPBOARD = False


# =========================
# CONFIG
# =========================

CHARSETS = ["utf-8", "iso-8859-1", "utf-7", "x"]
ENCODINGS = ["q", "b"]

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

# =========================
# MAIL DISCREPANCES
# =========================

# =========================
# ENCODERS
# =========================

def q_encode_force(data: bytes) -> str:
    """
    RFC 2047 Q-encoding FORZADO
    Todos los bytes -> =XX
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
    RFC 2045 Base64 con padding
    """
    return base64.b64encode(data).decode("ascii")


def encode_imap_utf7_full_from_bytes(raw: bytes) -> bytes:
    """
    IMAP UTF-7 COMPLETO sobre TODO el payload
    bytes -> latin-1 -> UTF-16BE -> Base64 modificado -> &...-
    """
    text = raw.decode("latin-1")                      #### modificado
    utf16 = text.encode("utf-16-be")                   #### modificado
    b64 = base64.b64encode(utf16).decode("ascii")     #### modificado
    b64 = b64.replace("/", ",").rstrip("=")           #### modificado
    return f"&{b64}-".encode("ascii")                  #### modificado

def detect_specials(raw: bytes) -> set[int]:
    specials = set()

    # 1) Control y no-ASCII
    for b in raw:
        if b < 0x20 or b >= 0x7F:
            specials.add(b)

    # 2) Puntuación seleccionada por el usuario
    for v in PUNCTUATION.values():
        specials |= set(v)

    # 3) Control chars seleccionados
    for v in CONTROL_CHARS.values():
        specials |= set(v)

    # 4) Secuencias especiales
    for v in SPECIAL_SEQUENCES.values():
        specials |= set(v)

    # 5) Separadores semánticos dentro del texto del usuario
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
    Devuelve una lista de encoded-words
    """
    results = []

    # =========================
    # CHARSET PHASE
    # =========================

    if charset == "utf-7":
        data = encode_imap_utf7_full_from_bytes(raw)   #### modificado
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
            # Variante A: UTF-7 sin Q forzado
            results.append(
                f"=?utf-7?q?{data.decode('ascii', 'ignore')}?="  #### modificado
            )

            # Variante B: solo '&' escapado
            escaped = data.replace(b"&", b"=26")        #### modificado
            results.append(
                f"=?utf-7?q?{escaped.decode('ascii', 'ignore')}?="  #### modificado
            )

        else:
            q = q_encode_force(data)
            results.append(f"=?{charset}?q?{q}?=")

    else:
        raise ValueError("\033[91m[ ERROR ] Encoding inválido\033[0m")

    # =========================
    # NUEVAS VARIANTES PARCIALES (A MAYORES)
    # =========================

    specials = detect_specials(raw)

    if specials:

        # --- Q parcial en cualquier charset ---
        partial_q = q_encode_partial(raw, specials)
        results.append(f"=?{charset}?q?{partial_q}?=")

        # --- UTF-7 parcial ---
        utf7_partial = utf7_encode_partial(raw, specials)
        results.append(f"=?utf-7?q?{utf7_partial.decode('ascii','ignore')}?=")

        # --- UTF-7 parcial + Q solo sobre '&' ---
        q_on_amp = q_encode_partial(utf7_partial, {ord('&')})
        results.append(f"=?utf-7?q?{q_on_amp}?=")


    return results


# =========================
# PAYLOAD BUILDERS
# =========================

def build_payload(base: str, punct: bytes | None, control: bytes | None) -> bytes:
    """
    Construye el payload EXACTAMENTE como si lo metiera el usuario
    """
    raw = base.encode("latin-1")

    if punct is not None:
        raw += punct                                  #### modificado

    if control is not None:
        raw += control                                #### modificado

    return raw


def generate_all(raw: bytes):
    """
    Aplica todos los charset + encoding al MISMO payload
    """
    results = []
    for cs in CHARSETS:
        for enc in ENCODINGS:
            results.extend(encode_payload(raw, cs, enc))
    return results

# =========================
# PUNNYCODE
# =========================

def generate_equivalences(base_char):
    """Generates all Unicode equivalents of a character"""
    equivalences = []
    for codepoint in range(0x20, unicode_max + 1):
        try:
            char = chr(codepoint)
        except ValueError:
            continue
        try:
            if collator.compare(char, base_char) == 0:
                equivalences.append(char)
        except Exception:
            continue
    return equivalences

def parse_input(user_input):
    """Detects if input is email or domain"""
    if "@" in user_input:
        local, domain = user_input.split("@", 1)
        print(f"\n\033[96m[ DETECTED EMAIL ]\033[0m  \033[92mLocal-part='{local}'\033[0m, \033[92mDomain='{domain}'\033[0m")
        #print(f"\nDetected email. Local-part='{local}', domain='{domain}'")
        return domain, local
    else:
        return user_input, None

def find_first_letter(domain, letters):
    for i, c in enumerate(domain):
        if c.lower() in letters:
            return c, i
    return None, None

def generate_punycode_variants(domain, letter, pos, unique_only=False, local_part=None):
    print("\n\033[96m[ PUNYCODE VARIANTS ]\033[0m")
    print("\033[93mScanning Unicode blocks to generate variants... (this may take a few seconds)\033[0m")
    start_time = time.time()
    variants = generate_equivalences(letter)
    print(f"\033[92mDone. Candidates found: {len(variants)}\033[0m\n")

    valid_punycode = {}
    for v in variants:
        if unique_only and v.lower() in [x.lower() for x in valid_punycode.values()]:
            continue
        try:
            mutated_domain = domain[:pos] + v + domain[pos+1:]
            puny = mutated_domain.encode("idna").decode("ascii")
            valid_punycode[puny] = v
        except Exception:
            continue

    elapsed = time.time() - start_time
    print(f"\033[92m[ INFO ] Valid punycode variants (unique): {len(valid_punycode)}\033[0m")
    print(f"\033[96m[ INFO ] Elapsed time: {elapsed:.2f}s\033[0m\n")

    # Numerar y preparar lista raw
    numbered_list = []
    raw_list = []
    for idx, (puny, char) in enumerate(valid_punycode.items(), 1):
        if local_part:
            full = f"{local_part}@{puny}"
        else:
            full = puny
        numbered_list.append(f"{idx}. {full} -> {char}")
        raw_list.append(full)

    # Mostrar numerados
    for line in numbered_list:
        print(line)

    print("\n")  # Separador
    # Mostrar solo punycodes / dominios / emails
    for item in raw_list:
        print(item)

    # Copiar al clipboard
    pyperclip.copy("\n".join(raw_list))
    print("\n\033[92m[ OK ]  All punycode variants copied to clipboard\033[0m\n")

    return valid_punycode, raw_list

def test_working_variant(valid_dict):
    """Ask user which variant worked and decode back to Unicode"""
    # Preguntar si quiere usar el usuario
    use_variant = input("\033[93mDo you want to check which variant worked? (y/n): \033[0m").strip().lower()
    if use_variant != "y":
        print("\n\033[96m[ INFO ] Skipping variant check.\033[0m\n")
        return
    print("\n\033[96m[ INPUT ] Enter punycode that worked (full domain or email)\033[0m")
    user_input = input("\033[93m> \033[0m").strip()
    # extract domain from email if needed
    if "@" in user_input:
        local, domain_input = user_input.split("@", 1)
    else:
        domain_input = user_input
    char_found = valid_dict.get(domain_input)
    if char_found:
        print(f"\n\033[92m[ SUCCESS ]\033[0m Variant corresponds to Unicode character: '{char_found}' (U+{ord(char_found):04X})\n")
    else:
        print(f"\n\033[91m[ ERROR ]\033[0m Variant not found in generated list.\n")

def punycode_menu():
    while True:
        # Menu header
        print("\n\033[96m[ PUNYCODE :: MODE]\033[0m\n")

        # Options
        print("  \033[92m(1)\033[0m  Generate variants for a single vowel")
        print("  \033[92m(2)\033[0m  Generate variants for a single consonant")
        print("  \033[92m(3)\033[0m  First vowel + first consonant  \033[93m[ WARNING: may overload the service ]\033[0m")
        print("  \033[92m(4)\033[0m  Back\n")

        # User input
        choice = input("\033[93m> \033[0m").strip()

        letters_vowel = "aeiou"
        letters_consonant = "bcdfghjklmnpqrstvwxyz"

        if choice in ["1", "2", "3"]:
            print("\n\033[96m[ INPUT ]\033[0m  Enter domain or email to process")
            user_input = input("\033[93m> \033[0m").strip()
            domain, local_part = parse_input(user_input)

            if choice == "1":
                letter, pos = find_first_letter(domain, letters_vowel)
                if letter is None:
                    print("\n\033[91m[ ERROR ] No vowel found in domain.\033[0m\n")
                    continue
                print(f"\n\033[96m[ INFO ]\033[0m First vowel found: \033[92m'{letter}'\033[0m at position \033[92m{pos}\033[0m\n")
                valid_dict, puny_list = generate_punycode_variants(domain, letter, pos, local_part=local_part)
                test_working_variant(valid_dict)

            elif choice == "2":
                letter, pos = find_first_letter(domain, letters_consonant)
                if letter is None:
                    print("\n\033[91m[ ERROR ] No consonant found in domain.\033[0m\n")
                    continue
                    print(f"\n\033[96m[ INFO ]\033[0m First consonant found: \033[92m'{letter}'\033[0m at position \033[92m{pos}\033[0m\n")
                valid_dict, puny_list = generate_punycode_variants(domain, letter, pos, local_part=local_part)
                test_working_variant(valid_dict)

            else:  # choice == "3"
                print("\n\033[93m[ WARNING ] This option may overload the service\033[0m\n")

                combined_valid_dict = {}
                combined_list = []

                # Primera vocal
                vowel, pos_v = find_first_letter(domain, letters_vowel)
                if vowel:
                    print(f"\n\033[96m[ INFO ]\033[0m First vowel found: \033[92m'{vowel}'\033[0m at position \033[92m{pos_v}\033[0m")
                    v_dict, v_list = generate_punycode_variants(domain, vowel, pos_v, local_part=local_part)
                    combined_list.extend(v_list)
                    combined_valid_dict.update(v_dict)
                else:
                    print("\033[91m[ ERROR ] No vowel found in domain.\033[0m\n")

                # Primera consonante
                consonant, pos_c = find_first_letter(domain, letters_consonant)
                if consonant:
                    print(f"\n\033[96m[ INFO ]\033[0m First consonant found: \033[92m'{consonant}'\033[0m at position \033[92m{pos_c}\033[0m")
                    c_dict, c_list = generate_punycode_variants(domain, consonant, pos_c, local_part=local_part)
                    combined_list.extend(c_list)
                    combined_valid_dict.update(c_dict)
                else:
                    print("\033[91m[ ERROR ] No consonant found in domain.\033[0m\n")

                # Mostrar TODO en un único listado numerado
                if combined_list:
                    print("\n\033[96m[ COMBINED PUNYCODE VARIANTS ]\033[0m")
                    for idx, item in enumerate(combined_list, 1):
                        print(f"\033[92m{idx}.\033[0m {item}")
                    pyperclip.copy("\n".join(combined_list))
                    print("\n\033[92m[ OK ] All punycode variants (vowel + consonant) copied to clipboard\033[0m\n")

                # Preguntar si funcionó alguna
                if combined_valid_dict:
                    test_working_variant(combined_valid_dict)

        elif choice == "4":
            break
        else:
            print("\033[91m[ ERROR ] Invalid choice, try again...\033[0m\n")



# =========================
# MAIN
# =========================

def encoded_menu():
    while True:
        print("\n\033[96m[ ENCODED‑WORD :: MODE ]\033[0m\n")
        print("  \033[92m(1)\033[0m  Single payload")
        print("  \033[92m(2)\033[0m  Fuzzer   \033[93m[ WARNING: may overload the service ]\033[0m")
        print("  \033[92m(3)\033[0m  Back\n")

        mode = input("\033[93m> \033[0m").strip()

        if mode == "3":
            break

        print("\n\033[96m[ INPUT ]  Enter the base email or text to process\033[0m")
        base = input("\033[93m> \033[0m ")
        all_results = []

        if mode == "1":
            print("\n\033[96m[ SINGLE PAYLOAD MODE ]\033[0m\n")

            punct = None
            if input("\033[93mAdd punctuation? (y/n): \033[0m").lower() == "y":
                for i, p in enumerate(PUNCTUATION, 1):
                    print(f"{i}. {p}")
                punct = list(PUNCTUATION.values())[int(input("\033[93m> \033[0m")) - 1]

            print("\n\033[96m[ CONTROL CHARACTERS ]\033[0m")
            print("Select control characters (e.g. 1,5)\n")
            all_ctrl = list(CONTROL_CHARS.items())
            for i, (n, _) in enumerate(all_ctrl, 1):
                print(f"{i}. {n}")

            selected = input("\n\033[93m> \033[0m").split(",")

            control = b""
            for i in selected:
                control += all_ctrl[int(i) - 1][1]

            raw = build_payload(base, punct, control)
            all_results = generate_all(raw)

        elif mode == "2":
            print("\n\033[96m[ FUZZER MODE ]\033[0m\n")

            punct_list = [None] + list(PUNCTUATION.values())
            control_list = [v for k, v in CONTROL_CHARS.items() if k != "NONE"]
            special_list = list(SPECIAL_SEQUENCES.values())

            for p in punct_list:

                # base + punctuation
                raw = build_payload(base, p, b"")
                all_results.extend(generate_all(raw))

                # base + punctuation + 1 control
                for c in control_list:
                    raw = build_payload(base, p, c)
                    all_results.extend(generate_all(raw))

                # base + punctuation + 1 special sequence
                for s in special_list:
                    raw = base.encode("latin-1")
                    if p:
                        raw += p
                    raw += s
                    all_results.extend(generate_all(raw))
        else:
            print("\n\033[91m[ ERROR ]  Invalid mode selected\033[0m\n")
            sys.exit(1)

        print("\n\033[96m[ RESULTS ]\033[0m\n")
        #final = "\n".join(all_results)
        unique = list(dict.fromkeys(all_results))
        final = "\n".join(unique)
        print(final)

        if CLIPBOARD:
            pyperclip.copy(final)
            if mode == "2":
                print("\n\033[93m[ WARNING ]  This option may overload the service\033[0m")
            print("\n\033[92m[ OK ]       Payloads copied to clipboard\033[0m\n")

def main():
    while True:
        print("\n\033[92m[ MAIN MENU ]\033[0m\n")
        print("  [1]  Encoded‑Word  ·  Local Part")
        print("  [2]  Punycode      ·  Domain")
        print("  [3]  Exit\n")
        choice = input("\033[93m> \033[0m").strip()
        if choice == "1":
            encoded_menu()
        elif choice == "2":
            punycode_menu()
        elif choice == "3":
            print("\n\033[91m[ EXITING RFCUT ]\033[0m\n")
            break
        else:
            print("\033[91m[ INVALID CHOICE ]  Try again...\033[0m\n")

if __name__ == "__main__":
    print(r"""
██████╗ ███████╗ ██████╗██╗   ██╗████████╗
██╔══██╗██╔════╝██╔════╝██║   ██║╚══██╔══╝
██████╔╝█████╗  ██║     ██║   ██║   ██║
██╔══██╗██╔══╝  ██║     ██║   ██║   ██║
██║  ██║██║     ╚██████╗╚██████╔╝   ██║
╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═════╝    ╚═╝

        break the mail standard
               by b3xal
""")
    main()
