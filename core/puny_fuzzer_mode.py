import subprocess
from utils.ui import *

def malformed_punycode_mode():
    while True:
        print("\n\033[96m[ PUNYCODE :: MALFORMED MODE ]\033[0m\n")
        print("  \033[92m(1)\033[0m  IDN PHP library")
        print("  \033[92m(2)\033[0m  Back\n")

        choice = input("\033[93m> \033[0m").strip()

        if choice == "2":
            return

        if choice != "1":
            print("\033[91m[ ERROR ] Invalid choice\033[0m")
            continue

        # Tag selection
        print("\n\033[96m[ SELECT TAG TO GENERATE ]\033[0m\n")
        print("  (1) <script")
        print("  (2) <img")
        print("  (3) <style")
        print("  (4) <custom\n")

        tag_choice = input("\033[93m> \033[0m").strip()

        if tag_choice == "1":
            tag = "script"
        elif tag_choice == "2":
            tag = "img"
        elif tag_choice == "3":
            tag = "style"
        elif tag_choice == "4":
            tag = input("\n\033[96mEnter custom tag: \033[0m").strip()
        else:
            print("\033[91m[ ERROR ] Invalid tag choice\033[0m")
            continue

        before = f"poc@xn--{tag}-$c1$1$2$3"
        matches = "@<@"
        contains = f"@<{tag}@"

        cmd = [
            "php", "core/puny-fuzzer-cli.php",
            f"--before={before}",
            f"--matches={matches}",
            f"--contains={contains}"
        ]

        print("\n\033[96m[ FUZZING IN PROGRESS ]\033[0m\n")

        result = subprocess.run(cmd, capture_output=True, text=True)

        output = result.stdout

        # Extract result nicely
        input_line = ""
        after_line = ""

        for line in output.splitlines():
            if line.startswith("Input:"):
                input_line = line.replace("Input:", "").strip()
            if line.startswith("After:"):
                after_line = line.replace("After:", "").strip()

        if input_line and after_line:
            print("\n\033[92m[ MALFORMED PUNYCODE GENERATED ]\033[0m\n")
            print(f"Input:  \033[93m{input_line}\033[0m")
            print(f"After:  \033[91m{after_line}\033[0m\n")
        else:
            print("\033[91m[ ERROR ] No valid payload found\033[0m\n")
