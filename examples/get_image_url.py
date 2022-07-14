import neko.providers
import asyncio
import aiohttp

async def main():
    async with aiohttp.ClientSession() as session:
        provider = neko.providers.NekobotProvider(session, extras={})
        url = await provider.fetch_image('neko')

        print(url)

asyncio.run(main())
