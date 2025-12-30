import time, random, string, idna
from utils.ui import *
from utils.clipboard import copy
from utils.config import *
from core.fuzzers import malformed_punycode_fuzzer

def insert_tag_into_domain(email: str, tag: str) -> str:
    if "@" not in email:
        raise ValueError("Invalid email format")

    local, domain = email.split("@", 1)

    # If no dot: append directly
    if "." not in domain:
        new_domain = domain + tag
    else:
        parts = domain.rsplit(".", 1)
        new_domain = parts[0] + tag + "." + parts[1]

    return f"{local}@{new_domain}"


