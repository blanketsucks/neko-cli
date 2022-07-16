from typing import Dict, List, Any

import aiohttp

from neko.providers.abc import Provider

class WaifupicsProvider(Provider):
    BASE_URL = 'https://api.waifu.pics/'

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any], debug: bool = False):
        super().__init__(session, extras=extras, debug=debug)
        self.nsfw: bool = extras.pop('nsfw', False)

        self._cache: List[str] = []

    def get_cached_images(self) -> List[str]:
        return self._cache.copy()

    async def fetch_image(self, type: str) -> str:
        if not self._cache:
            self._cache = await self.fetch_many(type)

        return self._cache.pop()

    async def fetch_many(self, type: str) -> List[str]:
        route = f'many/sfw/{type}'
        if self.nsfw:
            route = f'many/nsfw/{type}'

        data = await self.request(route, method='POST', json={'exclude': []})
        return data['files']

    async def fetch_categories(self) -> Dict[str, int]:
        data = await self.request('endpoints')
        categories: Dict[str, int] = {}

        categories.update({category: -1 for category in data['sfw']})
        categories.update({category: -1 for category in data['nsfw']})

        return categories
