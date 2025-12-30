import subprocess

CLIPBOARD = True

def copy(text: str):
    try:
        subprocess.run(
            ['xclip', '-selection', 'clipboard'],
            input=text.encode('utf-8'),
            check=True
        )
    except FileNotFoundError:
        msg = "xclip is not installed. Install it with: sudo apt install xclip"
        print(f"\n\033[91m[ ERROR ] {msg}\033[0m\n")
    except subprocess.CalledProcessError as e:
        msg = f"Error copying to clipboard: {e}"
        print(f"\n\033[91m[ ERROR ] {msg}\033[0m\n")
