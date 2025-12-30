from utils.ui import *
from utils.clipboard import copy
from utils.config import *
import random, idna
import re

def generate_random_component(template: str):
    result = template
    for i in range(1, 10):
        result = result.replace(f"${i}", str(random.randint(0, 9)))
        result = result.replace(f"$c{i}", random.choice(CHARS))
    for i in range(1, 3):
        result = result.replace(f"$w{i}", random.choice(WHITESPACE))
    return result

def decode_puny_python(domain: str):
    try:
        return idna.decode(domain)
    except Exception:
        return None

def fuzz_email(base_email: str, inject: str, iterations: int = 1000):
    if "@" not in base_email:
        raise ValueError("Correo inválido")
    local, domain = base_email.split("@", 1)

    # Separar nombre y extensión
    if "." in domain:
        domain_name, ext = domain.rsplit(".", 1)
        ext = "." + ext
    else:
        domain_name = domain
        ext = ""

    print(f"\n[INFO] Starting fuzzing '{base_email}' injecting '{inject}' ...\n")

    for _ in range(iterations):
        # Candidate con la inyección
        candidate_domain = domain_name + inject + ext
        candidate_email = f"{local}@{candidate_domain}"

        # Convertir solo caracteres no ASCII o inválidos
        try:
            # idna solo acepta labels válidos, pero forcemos la inyección
            # Cada label separado por '.', codificamos por separado
            labels = candidate_domain.split(".")
            encoded_labels = []
            for label in labels:
                # Comprobamos si hay caracteres inválidos
                if any(c in "<>\"\\; " or ord(c) > 127 for c in label):
                    # Forzar Punycode
                    encoded_labels.append(idna.encode(label).decode("ascii"))
                else:
                    encoded_labels.append(label)
            encoded_domain = ".".join(encoded_labels)
        except Exception:
            continue

        # Reconstruir correo
        candidate_email_encoded = f"{local}@{encoded_domain}"

        # Mostrar siempre
        print(f"{candidate_email_encoded} → {candidate_email}")
        copy(candidate_email_encoded)  # Copia la última coincidencia
        return candidate_email_encoded, candidate_email

    print("No matches found.")
    return None, None

def malformed_punycode_fuzzer(email, injection, iterations=30000):

    print(f"[INFO] Launching PHP malformed punycode fuzzer...")

    output = run_php_fuzzer(email, injection, iterations)

    if not output:
        return []

    results = []

    for line in output.splitlines():
        if line.startswith("INPUT:"):
            current_input = line.replace("INPUT:", "").strip()
        if line.startswith("OUTPUT:"):
            current_output = line.replace("OUTPUT:", "").strip()
            results.append((current_input, current_output))

    return results

def malformed_punycode_mode():
    print("\n\033[96m[ MALFORMED PUNYCODE AUTOMATIC MODE ]\033[0m\n")

    email = input("Enter a valid email: ").strip()
    injection = input("Enter what you want to inject: ").strip()

    print("\n\033[96mSelect decoding engine:\033[0m\n")
    print("  \033[92m(1)\033[0m  PHP IDN Library  \033[93m[ Algo26\\IdnaConvert ]\033[0m")
    input("\n\033[93m> \033[0m")  # por ahora solo hay uno

    print("\n\033[96m[ INFO ] Starting fuzzing...\033[0m\n")

    matches = malformed_punycode_fuzzer(email, injection)

    if not matches:
        print("\n\033[91m[ INFO ] No malformed punycode found.\033[0m\n")
        return

    print("\n\033[92m[ RESULTS ]\033[0m\n")
    for p, d in matches:
        print(f"{p}  →  {d}")
