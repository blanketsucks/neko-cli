from typing import Dict

from neko.providers.abc import Provider

class NekobotProvider(Provider):
    BASE_URL = 'https://nekobot.xyz/api/image'

    async def fetch_image(self, type: str) -> str:
        params = {'type': type}
        data = await self.request(params=params)

        return data['message']
        
    async def fetch_categories(self) -> Dict[str, int]:
        data = await self.request()
        return data['stats']
