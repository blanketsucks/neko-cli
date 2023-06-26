from typing import Any, Dict, List, NamedTuple

import aiohttp

from neko.providers.abc import CachableProvider
from neko.providers.providers import register

class WaifuimImage(NamedTuple):
    file: str
    tags: List[str]
    source: str
    url: str

@register('waifu.im')
class WaifuimProvider(CachableProvider[WaifuimImage]):
    BASE_URL = 'https://api.waifu.im/'

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any]):
        super().__init__(session, extras=extras)
        self.nsfw: bool = extras.pop('nsfw', False)

    async def request(self, type: str, **params: Any) -> Dict[str, Any]:
        params['selected_tags'] = type
        params.setdefault('is_nsfw', 'true' if self.nsfw else 'false')

        return await super().request('random', params=params)

    async def _fetch_many(self, type: str) -> List[WaifuimImage]:
        data = await self.request(type, many='true')
        images: List[WaifuimImage] = []

        for payload in data['images']:
            image = WaifuimImage(
                file=payload['file'],
                tags=[tag['name'] for tag in payload['tags']],
                source=payload['source'],
                url=payload['url'],
            )

            images.append(image)

        return images

    async def fetch_image(self, type: str) -> str:
        if not self._cache:
            self._cache = await self._fetch_many(type)

        image = self._cache.pop()
        return image.url

    async def fetch_many(self, type: str) -> List[str]:
        images = await self._fetch_many(type)
        return [image.url for image in images]

    async def fetch_categories(self) -> Dict[str, int]:
        data = await self.request('tags', params={'full': 'on'})
        categories: Dict[str, int] = {}

        categories.update({tag['name']: -1 for tag in data['versatile']})
        categories.update({tag['name']: -1 for tag in data['nsfw']})

        return categories
