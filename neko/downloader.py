from typing import Any, Dict

import aiohttp
import pathlib
import asyncio

from .utils import Colors

class Downloader:
    __slots__ = ('session', 'url', 'path', 'debug')

    def __init__(
        self, 
        session: aiohttp.ClientSession, 
        url: str,
        path: pathlib.Path,
        *,
        debug: bool = False
    ) -> None:
        self.session = session
        self.url = url
        self.path = path
        self.debug = debug

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.session.loop

    def get_file_extension(self, content_type: str) -> str:
        return content_type.split('/')[-1]

    def get_download_path(self, ident: str, extension: str) -> pathlib.Path:
        return (self.path / f'{ident}.{extension}')

    def has_extension(self, ident: str) -> bool:
        return len(ident.split('.')) > 1

    async def chunk(self, response: aiohttp.ClientResponse):
        while True:
            chunk = await response.content.read(1024)
            if not chunk:
                break

            yield chunk

    async def write(self, path: pathlib.Path, response: aiohttp.ClientResponse) -> None:
        file = path.open('wb')
        async for chunk in self.chunk(response):
            file.write(chunk)

        file.flush()
        file.close()

        if self.debug:
            fmt = f"{Colors.white}- {path.name}{Colors.reset}: {Colors.green}Successfully Downloaded.{Colors.reset}"
            print(fmt)

    async def fetch_download_path(self, ident: str) -> pathlib.Path:
        headers = await self.fetch_headers()
        if not self.has_extension(ident):
            extension = self.get_file_extension(headers['Content-Type'])
            path = self.get_download_path(ident, extension)
        else:
            path = self.path / ident

        return path

    async def fetch_headers(self) -> Dict[str, Any]:
        async with self.session.head(self.url) as response:
            return dict(response.headers)

    async def download(self, ident: str) -> bool:
        async with self.session.get(self.url) as response:
            if response.status != 200:
                if self.debug:
                    fmt = f"{Colors.white}- {ident}{Colors.reset}: {Colors.red}Failed to download with status code '{response.status}'.{Colors.reset}"
                    print(fmt)

                return False

            if not self.has_extension(ident):
                extension = self.get_file_extension(response.headers['Content-Type'])
                path = self.get_download_path(ident, extension)
            else:
                path = self.path / ident

            if path.suffix not in ('.jpg', '.jpeg', '.png', '.gif'):
                if self.debug:
                    fmt = f"{Colors.white}- {ident}{Colors.reset}: {Colors.red}Unsupported file type '{path.suffix}'.{Colors.reset}"
                    print(fmt)

                return False

            await self.write(path, response)
            return True
