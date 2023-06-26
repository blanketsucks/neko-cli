from typing import Iterable, Iterator, Tuple, TypeVar, Callable, Any

from enum import Enum
import asyncio
import itertools

T = TypeVar('T')

class Colors(str, Enum):
    red = '\u001b[1;31m'
    green = '\u001b[1;32m'
    yellow = '\u001b[1;33m'
    white = '\u001b[1;37m'
    reset = '\u001b[0m'

def get_input(prompt: str) -> str:
    return input(prompt.format_map(Colors.__members__))

def format_exception(exc: BaseException) -> str:
    name = exc.__class__.__name__
    message = ' '.join(exc.args)

    return f'{name}: {message}'

def chunk(iterable: Iterable[T], size: int) -> Iterator[Tuple[T]]:
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            return

        yield chunk

async def to_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)