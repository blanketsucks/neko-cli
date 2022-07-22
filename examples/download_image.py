from neko.providers import NekobotProvider
from neko.downloader import Downloader
import aiohttp
import asyncio
import pathlib

async def main():
    async with aiohttp.ClientSession() as session:
        provider = NekobotProvider(session, extras={})
        url = await provider.fetch_image('neko')

        download_path = pathlib.Path('path/to/download/dir')
        downloader = Downloader(provider, download_path)

        # Returns a boolean indicating whether or not the download succeeded.
        # It's up the user to check if the file exists already.
        await downloader.download(url)

asyncio.run(main())