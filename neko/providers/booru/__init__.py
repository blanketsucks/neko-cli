from typing import List, NamedTuple, Dict, Any

import aiohttp
import urllib.parse

from neko.providers.abc import CachableProvider
from neko.providers.providers import register

BASE_URL = 'https://booru.io/api/legacy'

class BooruImage(NamedTuple):
    key: str
    content_type: str
    width: int
    height: int
    tags: List[str]
    transforms: List[str]

    @property
    def url(self) -> str:
        transform = self.transforms[0]
        return f'{BASE_URL}/data/{transform}'

@register('booru.io')
class BooruProvider(CachableProvider[BooruImage]):
    BASE_URL = BASE_URL
    REQUIRES_EXTRAS = True

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any]):
        super().__init__(session, extras=extras)

        self.params: Dict[str, Any] = {}

        self.cursor = extras.pop('cursor', 0)
        self.tags: List[str] = extras.pop('tags', [])

        self.params['query'] = ' '.join(self.tags)
        self.params['cursor'] = self.cursor

    async def _fetch_many(self) -> List[BooruImage]:
        data = await self.request('/query/entity', params=self.params)
        try:
            self.params['cursor'] = int(data['cursor'])
        except KeyError:
            self.params['cursor'] = 0
            
        return [
            BooruImage(
                key=image['key'],
                content_type=image['contentType'],
                width=image['attributes']['width'],
                height=image['attributes']['height'],
                tags=list(image['tags'].keys()),
                transforms=list(image['transforms'].values()),
            )
            for image in data['data']
        ]

    async def fetch_image(self, _: str = '') -> str:
        if not self._cache:
            self._cache = await self._fetch_many()

        image = self._cache.pop()
        return image.url

    async def fetch_many(self, _: str = '') -> List[str]:
        images = await self._fetch_many()
        return [image.url for image in images]
    
    async def fetch_categories(self) -> Dict[str, int]:
        return {}

    def get_identifier_from_url(self, url: str) -> str:
        return urllib.parse.urlparse(url).path.split('/')[-2]