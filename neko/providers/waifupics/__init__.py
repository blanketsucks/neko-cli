from typing import Dict, List

from neko.providers.abc import Provider

class WaifupicsProvider(Provider):
    BASE_URL = 'https://api.waifu.pics/'

    async def fetch_image(self, type: str) -> str:
        async with self.session.get(self.BASE_URL + f'nsfw/{type}') as response:
            data = await response.json()
            return data['url']

    async def fetch_many(self, type: str) -> List[str]:
        data = {'exclude': []}
        async with self.session.post(self.BASE_URL + f'many/nsfw/{type}', json=data) as response:
            data = await response.json()
            return data['files']

    async def fetch_categories(self) -> Dict[str, int]:
        async with self.session.get(self.BASE_URL + 'endpoints') as response:
            categories: Dict[str, int] = {}
            data = await response.json()

            categories.update({category: -1 for category in data['sfw']})
            categories.update({category: -1 for category in data['nsfw']})

            return categories
