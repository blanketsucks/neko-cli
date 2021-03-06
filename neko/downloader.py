from typing import Any, Mapping

import aiohttp
import pathlib
import asyncio

from .providers import Provider
from .utils import Colors, format_exception

class Downloader:
    __slots__ = ('provider', 'path', 'debug')

    def __init__(
        self, 
        provider: Provider,
        path: pathlib.Path,
        *,
        debug: bool = False
    ) -> None:
        self.path = path
        self.provider = provider
        self.debug = debug

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.provider.session

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.session.loop

    def get_file_extension(self, content_type: str) -> str:
        """
        Parses the file extension from a Content-Type header.
        For example, `image/jpg` becomes `jpg`.

        Parameters
        ----------
        content_type: :class:`str`
            The Content-Type header.
        """
        return content_type.split('/')[-1]

    def get_download_path(self, identifier: str, extension: str) -> pathlib.Path:
        """
        Gets the download path from an identifier and file extension.
        The :class:`pathlib.Path` may not exist.

        Parameters
        ----------
        identifier: :class:`str`
            The identifier of the file.
        extension: :class:`str`
            The extension of the file.
        """
        return (self.path / identifier).with_suffix(extension)

    def has_extension(self, identifier: str) -> bool:
        """
        Returns whether or not the identifier has a file extension.

        Parameters
        ----------
        identifier: :class:`str`
            The identifier of the file.
        """
        return len(identifier.split('.')) > 1

    def get_download_path_from_headers(self, identifier: str, headers: Mapping[str, Any]) -> pathlib.Path:
        """
        Gets the download path from an identifier and headers.
        The :class:`pathlib.Path` may not exist.

        Parameters
        ----------
        identifier: :class:`str`
            The identifier of the file.
        headers: :class:`dict`
            The headers.
        """
        if not self.has_extension(identifier):
            extension = self.get_file_extension(headers['Content-Type'])
            path = self.get_download_path(identifier, extension)
        else:
            path = self.path / identifier

        return path

    async def chunk(self, response: aiohttp.ClientResponse, *, chunk_size: int = 1024):
        """
        Chunks a response into chunks of size `chunk_size`.

        Parameters
        ----------
        response: :class:`aiohttp.ClientResponse`
            The response to chunk.
        chunk_size: :class:`int`
            The size of each chunk. Defaults to 1024.        
        """
        while True:
            chunk = await response.content.read(chunk_size)
            if not chunk:
                break

            yield chunk

    async def write(self, path: pathlib.Path, response: aiohttp.ClientResponse) -> None:
        """
        Writes the response to the given path.
        This creates a temporary file and then if the download succeeds, renames it to the final path else
        it deletes the file.

        Parameters
        ----------
        path: :class:`pathlib.Path`
            The path to write to.
        response: :class:`aiohttp.ClientResponse`
            The response to write.
        """
        tmp = path.with_suffix('.tmp')
        try:
            with tmp.open('wb') as file:
                async for chunk in self.chunk(response):
                    file.write(chunk)

            if self.debug:
                fmt = f"{Colors.white}- {path.name}{Colors.reset}: {Colors.green}Successfully Downloaded.{Colors.reset}"
                print(fmt)
        except Exception as e:
            tmp.unlink()
            
            if self.debug:
                exc = format_exception(e)

                fmt = f"{Colors.white}- {path.name}{Colors.reset}: {Colors.red}Failed to download due to {exc!r}.{Colors.reset}"
                print(fmt)
            else:
                raise e
        else:
            tmp.rename(path)

    async def fetch_download_path(self, url: str) -> pathlib.Path:
        """
        Fetches the download path from a given URL.
        This sends a HEAD request to the URL to retrieve the Content-Type header, and then uses that to determine the file extension.

        Parameters
        ----------
        url: :class:`str`
            The URL of the file.
        """
        headers = await self.fetch_headers(url)
        identifier = self.provider.get_identifier_from_url(url)

        return self.get_download_path_from_headers(identifier, headers)

    async def fetch_headers(self, url: str) -> Mapping[str, Any]:
        """
        Fetches the headers from a given URL.

        Parameters
        ----------  
        url: :class:`str`
            The URL of the file.
        """
        async with self.session.head(url) as response:
            return response.headers

        return {}

    async def download(self, url: str) -> bool:
        """
        Downloads the given URL.
        This function returns a boolean indicating whether or not the downloaded succeeded.

        Parameters
        -----------
        url: :class:`str`
            The URL of the file.
        """
        async with self.session.get(url) as response:
            identifier = self.provider.get_identifier_from_url(url)
            if response.status != 200:
                if self.debug:
                    fmt = f"{Colors.white}- {identifier}{Colors.reset}: {Colors.red}Failed to download with status code '{response.status}'.{Colors.reset}"
                    print(fmt)

                return False

            path = self.get_download_path_from_headers(identifier, response.headers)
            if path.suffix not in ('.jpg', '.jpeg', '.png', '.gif', '.webm', '.mp4'):
                if self.debug:
                    fmt = f"{Colors.white}- {identifier}{Colors.reset}: {Colors.red}Unsupported file type '{path.suffix}'.{Colors.reset}"
                    print(fmt)

                return False

            await self.write(path, response)

        return True
