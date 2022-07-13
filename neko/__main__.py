import asyncio

from .main import main

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    code = loop.run_until_complete(main())

    exit(code)