
import time
from icu import Collator, Locale
from utils.ui import *
from utils.clipboard import copy

collator = Collator.createInstance(Locale('en_US'))
collator.setStrength(collator.PRIMARY)
unicode_max = 0x10FFFF


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

def generate_punycode_variants(domain, letter, pos, unique_only=False, local_part=None, homograph_only=False):
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

    # Number and prepare raw list
    numbered_list = []
    raw_list = []

    idx = 1
    for puny, char in valid_punycode.items():

        # Punycode variant
        if local_part:
            puny_mail = f"{local_part}@{puny}"
            unicode_mail = f"{local_part}@{domain[:pos]}{char}{domain[pos+1:]}"
        else:
            puny_mail = puny
            unicode_mail = domain[:pos] + char + domain[pos+1:]

        #numbered_list.append(f"{idx}. {puny_mail} -> {char}")
        #raw_list.append(puny_mail)
        #idx += 1

        numbered_list.append(f"{idx}. {unicode_mail}")
        raw_list.append(unicode_mail)
        idx += 1
    # Show numbered
    for line in numbered_list:
        print(line)

    print("\n")

    # Show only punycodes / domains / emails
    raw_list = list(dict.fromkeys(raw_list))
    for item in raw_list:
        print(item)

    # Copy to clipboard
    try:
        copy("\n".join(raw_list))
        print("\n\033[92m[ OK ]  All homograph variants copied to clipboard\033[0m\n")
    except Exception as e:
        print(f"\n\033[91m[ ERROR ] Failed to copy to clipboard: {e}\033[0m\n")

    return valid_punycode, raw_list


def test_working_variant(valid_dict):
    """Ask user which variant worked and decode back to Unicode"""
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
