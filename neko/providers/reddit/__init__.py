from typing import List, Dict, Any, Literal, Optional, Tuple, overload, NamedTuple

import aiohttp
import asyncio

from neko.providers.abc import Provider
from neko.utils import Colors, error

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'

class RedditImage(NamedTuple):
    url: str
    name: str

class RedditProvider(Provider):
    BASE_URL = 'https://reddit.com/'

    def __init__(self, session: aiohttp.ClientSession, extras: Dict[str, Any]):
        super().__init__(session, extras)

        try:
            self.subreddit = extras.pop('subreddit')
            if not isinstance(self.subreddit, str):
                error('`subreddit` must be a string.')
        except KeyError:
            error('No subreddit specified.')

        self.sort = extras.pop('sort', 'hot')
        if not isinstance(self.sort, str):
            error('`sort` must be a string.')

        if self.sort not in ('hot', 'new', 'rising', 'top', 'controversial'):
            error('`sort` must be one of "hot", "new", "rising", "top" or "controversial".')

        self.session.headers['User-Agent'] = extras.pop('user_agent', USER_AGENT)
        self.last: Optional[str] = None

        self._cache: List[RedditImage] = []

    def get_cached_images(self) -> List[RedditImage]:
        return self._cache.copy()

    async def fetch_image(self, type: str) -> str:
        if not self._cache:
            # Cache the responses to avoid API calls
            self._cache = await self._fetch_many(type)

        image, name = self._cache.pop()
        self.last = name

        return image

    async def _fetch_many(self, _: str) -> List[RedditImage]:
        params: Dict[str, Any] = {'limit': 30, **self.extras}
        if self.last:
            params['after'] = self.last

        async with self.session.get(self.BASE_URL + f'r/{self.subreddit}/{self.sort}.json', params=params) as response:
            if response.status == 429:
                retry_after = float(response.headers['Retry-After'])
                print(f'{Colors.red}- Too many requests. Retrying in {retry_after} seconds.{Colors.reset}')

                await asyncio.sleep(retry_after)
                return await self._fetch_many(_)
            
            data = await response.json()

            images: List[RedditImage] = []

            for child in data['data']['children']:
                post = child['data']
                if post['is_self']:
                    continue

                if post.get('is_gallery', False):
                    images += await self.fetch_gallery(post['url'], post['name'])
                else:
                    images.append(RedditImage(post['url'], post['name']))

                self.last = post['name']

            return images

    async def fetch_many(self, type: str) -> List[str]:
        images = await self._fetch_many(type)
        return [image.url for image in images]

    async def fetch_gallery(self, url: str, name: str) -> List[RedditImage]:
        new_url = url.replace('gallery', 'comments') + '.json'
        async with self.session.get(new_url) as response:
            data = await response.json()

            images: List[RedditImage] = []

            medias = data[0]['data']['children'][0]['data']['media_metadata']
            for id, metadata in medias.items():
                extension = metadata['m'].split('/')[-1]
                images.append(RedditImage(f'https://i.redd.it/{id}.{extension}', name))

            return images

    async def fetch_categories(self) -> Dict[str, int]:
        return {}
    