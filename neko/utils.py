from typing import NoReturn

from enum import Enum

class Colors(str, Enum):
    red = '\u001b[1;31m'
    green = '\u001b[1;32m'
    white = '\u001b[1;37m'
    reset = '\u001b[0m'

def get_input(prompt: str) -> str:
    inp = input(prompt.format_map(Colors.__members__))
    if inp in ('q', 'quit', 'exit'):
        print(Colors.reset.value)
        exit(0)

    return inp

def error(msg: str) -> NoReturn:
    print(f'{Colors.red}- {msg}{Colors.reset}')
    exit(1)