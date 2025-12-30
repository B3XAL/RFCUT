def header(title):
    print(f"\n\033[96m[ {title} ]\033[0m\n")

def ok(msg):
    print(f"\033[92m[ OK ] {msg}\033[0m")

def warn(msg):
    print(f"\033[93m[ WARNING ] {msg}\033[0m")

def error(msg):
    print(f"\033[91m[ ERROR ] {msg}\033[0m")

def info(msg):
    print(f"\033[96m[ INFO ] {msg}\033[0m")
