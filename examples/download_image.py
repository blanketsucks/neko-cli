from neko.providers import NekobotProvider
from neko.downloader import Downloader
import aiohttp
import asyncio
import pathlib

async def main():
    async with aiohttp.ClientSession() as session:
        provider = NekobotProvider(session, {})
        url = await provider.fetch_image('neko')

        download_path = pathlib.Path('path/to/download/dir')

        # The debug keyword indicates whether or not to print messages to the console.
        downloader = Downloader(session, url, download_path, debug=False)

        # This identifier represents an identifier unique for this url.
        identifier = provider.get_identifier_from_url(url)

        # Returns a boolean indicating whether or not the download succeeded.
        # It's up the user to check if the file exists already.
        await downloader.download(identifier)

asyncio.run(main())