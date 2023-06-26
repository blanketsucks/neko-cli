from typing import Dict, List, Any

import aiohttp

from neko.providers.abc import CachableProvider
from neko.providers.providers import register

@register('waifu.pics')
class WaifupicsProvider(CachableProvider[str]):
    BASE_URL = 'https://api.waifu.pics/'

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any]):
        super().__init__(session, extras=extras)
        self.nsfw: bool = extras.pop('nsfw', False)

    async def fetch_image(self, category: str) -> str:
        if not self._cache:
            self._cache = await self.fetch_many(category)

        return self._cache.pop()

    async def fetch_many(self, category: str) -> List[str]:
        route = f'many/sfw/{category}'
        if self.nsfw:
            route = f'many/nsfw/{category}'

        data = await self.request(route, method='POST', json={'exclude': []})
        return data['files']

    async def fetch_categories(self) -> Dict[str, int]:
        data = await self.request('endpoints')
        categories: Dict[str, int] = {}

        categories.update({category: -1 for category in data['sfw']})
        categories.update({category: -1 for category in data['nsfw']})

        return categories
