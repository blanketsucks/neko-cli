from typing import Dict, List

from neko.providers.abc import Provider

class WaifupicsProvider(Provider):
    BASE_URL = 'https://api.waifu.pics/'

    async def fetch_image(self, type: str) -> str:
        data = await self.request(f'nsfw/{type}')
        return data['url']

    async def fetch_many(self, type: str) -> List[str]:
        data = await self.request(f'many/nsfw/{type}', many='true', json={'exclude': []})
        return data['files']

    async def fetch_categories(self) -> Dict[str, int]:
        data = await self.request('endpoints')
        categories: Dict[str, int] = {}

        categories.update({category: -1 for category in data['sfw']})
        categories.update({category: -1 for category in data['nsfw']})

        return categories
