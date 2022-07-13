from typing import List, Dict, Any, Literal, Optional, Tuple, overload

import aiohttp
import asyncio

from neko.providers.abc import Provider
from neko.utils import Colors, error

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'

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

        self.session.headers['User-Agent'] = USER_AGENT
        self.last: Optional[str] = None
        self.cache: List[Tuple[str, str]] = []

    async def fetch_image(self, type: str) -> str:
        if not self.cache:
            # Cache the responses to avoid API calls
            self.cache = await self.fetch_many(type, with_names=True)

        image, name = self.cache.pop()
        self.last = name

        return image

    @overload
    async def fetch_many(self, _: str) -> List[str]:
        ...
    @overload
    async def fetch_many(self, _: str, *, with_names: Literal[True]) -> List[Tuple[str, str]]:
        ...
    @overload
    async def fetch_many(self, _: str, *, with_names: Literal[False]) -> List[str]:
        ...
    async def fetch_many(self, _: str, *, with_names: bool = False) -> List[Any]:
        params: Dict[str, Any] = {'limit': 30, **self.extras}
        if self.last:
            params['after'] = self.last

        async with self.session.get(self.BASE_URL + f'r/{self.subreddit}/{self.sort}.json', params=params) as response:
            if response.status == 429:
                retry_after = float(response.headers['Retry-After'])
                print(f'{Colors.red}- Too many requests. Retrying in {retry_after} seconds.{Colors.reset}')

                await asyncio.sleep(retry_after)
                return await self.fetch_many(_, with_names=with_names) # type: ignore
            
            data = await response.json()

            images: List[str] = []
            names: List[str] = []

            for child in data['data']['children']:
                post = child['data']
                if post['is_self']:
                    continue

                images.append(post['url'])
                names.append(post['name'])

                self.last = post['name']

            if with_names:
                return list(zip(images, names))
            else:
                return images

    async def fetch_categories(self) -> Dict[str, int]:
        return {}
    