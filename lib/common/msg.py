from termcolor import cprint

def err(msg: str):
    cprint(f"error: {msg}", 'red')

def warn(msg: str):
    cprint(f"warning: {msg}", 'yellow')
