from core.encoders import *
from core.payloads import *
from core.homograph import *
from core.punycode import *
from core.fuzzers import *
from utils.ui import *
from core.puny_fuzzer_mode import *

# =========================
# PUNNYCODE - MENU
# =========================

def punycode_menu():
    while True:
        print("\n\033[96m[ PUNYCODE :: MAIN MODE ]\033[0m\n")
        print("  \033[92m(1)\033[0m  Homograph discovery")
        print("  \033[92m(2)\033[0m  Craft malformed Punycode")
        print("  \033[92m(3)\033[0m  Back\n")

        pre_choice = input("\033[93m> \033[0m").strip()

        if pre_choice == "1":
            homograph_mode()
        elif pre_choice == "2":
            malformed_punycode_mode()
        elif pre_choice == "3":
            break
        else:
            print("\033[91m[ ERROR ] Invalid choice, try again...\033[0m\n")


def homograph_mode():
    while True:
        # Menu header
        print("\n\033[96m[ PUNYCODE :: HOMOGRAPH MODE]\033[0m\n")

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
                valid_dict, puny_list = generate_punycode_variants(domain, letter, pos, local_part=local_part, homograph_only=True)
                #test_working_variant(valid_dict)

            elif choice == "2":
                letter, pos = find_first_letter(domain, letters_consonant)
                if letter is None:
                    print("\n\033[91m[ ERROR ] No consonant found in domain.\033[0m\n")
                    continue
                    print(f"\n\033[96m[ INFO ]\033[0m First consonant found: \033[92m'{letter}'\033[0m at position \033[92m{pos}\033[0m\n")
                valid_dict, puny_list = generate_punycode_variants(domain, letter, pos, local_part=local_part)
                #test_working_variant(valid_dict)

            else:  # choice == "3"
                print("\n\033[93m[ WARNING ] This option may overload the service\033[0m\n")

                combined_valid_dict = {}
                combined_list = []

                # First vowel
                vowel, pos_v = find_first_letter(domain, letters_vowel)
                if vowel:
                    print(f"\n\033[96m[ INFO ]\033[0m First vowel found: \033[92m'{vowel}'\033[0m at position \033[92m{pos_v}\033[0m")
                    v_dict, v_list = generate_punycode_variants(domain, vowel, pos_v, local_part=local_part)
                    combined_list.extend(v_list)
                    combined_valid_dict.update(v_dict)
                else:
                    print("\033[91m[ ERROR ] No vowel found in domain.\033[0m\n")

                # First consonant
                consonant, pos_c = find_first_letter(domain, letters_consonant)
                if consonant:
                    print(f"\n\033[96m[ INFO ]\033[0m First consonant found: \033[92m'{consonant}'\033[0m at position \033[92m{pos_c}\033[0m")
                    c_dict, c_list = generate_punycode_variants(domain, consonant, pos_c, local_part=local_part)
                    combined_list.extend(c_list)
                    combined_valid_dict.update(c_dict)
                else:
                    print("\033[91m[ ERROR ] No consonant found in domain.\033[0m\n")

                # Display ALL in a single numbered list
                if combined_list:
                    print("\n\033[96m[ COMBINED UNICODE / IDN VARIANTS ]\033[0m")
                    combined_list = list(dict.fromkeys(combined_list))
                    for idx, item in enumerate(combined_list, 1):
                        print(f"{item}")
                    copy("\n".join(combined_list))
                    print("\n\033[92m[ OK ] All IDN variants (vowel + consonant) copied to clipboard\033[0m\n")

                # Ask if any of them worked
                #if combined_valid_dict:
                    #test_working_variant(combined_valid_dict)

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

            #punct = None
            #if input("\033[93mAdd punctuation? (y/n): \033[0m").lower() == "y":
            #    for i, p in enumerate(PUNCTUATION, 1):
            #        print(f"{i}. {p}")
            #    punct = list(PUNCTUATION.values())[int(input("\033[93m> \033[0m")) - 1]

            print("\n\033[96m[ PUNCTUATION ]\033[0m")
            print("Select punctuation\n")

            punct = None
            all_punct = list(PUNCTUATION.items())

            for i, (name, _) in enumerate(all_punct, 1):
                print(f"{i}. {name}")

            choice = input("\n\033[93m> \033[0m").strip()

            if choice != "1":
                punct = all_punct[int(choice) - 1][1]

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

        if copy:
            copy(final)
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
