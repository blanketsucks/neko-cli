from typing import Dict

import asyncio

from neko.providers.abc import Provider
from neko.utils import Colors

class NekobotProvider(Provider):
    BASE_URL = 'https://nekobot.xyz/api/image'

    async def fetch_image(self, type: str) -> str:
        params = {'type': type}
        async with self.session.get(self.BASE_URL, params=params) as response:
            data = await response.json()
            if response.status == 429:
                retry_after = float(response.headers['Retry-After'])
                print(f'{Colors.red}- Too many requests. Retrying in {retry_after} seconds.{Colors.reset}')

                await asyncio.sleep(retry_after)
                return await self.fetch_image(type)

            return data['message']
        
    async def fetch_categories(self) -> Dict[str, int]:
        async with self.session.get(self.BASE_URL) as response:
            data = await response.json()
            return data['stats']
