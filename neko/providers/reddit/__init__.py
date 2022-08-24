from typing import List, Dict, Any, Optional, NamedTuple

import aiohttp
import re

from neko.providers.abc import CachableProvider
from neko.providers.utils import get_str_value
from neko.utils import Colors

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
REDDIT_GALLERY_REGEX = re.compile(r'https:\/\/www\.reddit\.com\/gallery\/.+')

class RedditImage(NamedTuple):
    url: str
    name: str

class RedditProvider(CachableProvider[RedditImage]):
    BASE_URL = 'https://reddit.com/'

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any], debug: bool = False):
        extras.pop('nsfw')
        super().__init__(session, extras=extras, debug=debug)

        self.subreddit = get_str_value(extras, 'subreddit')

        self.sort = extras.pop('sort', 'hot')
        if not isinstance(self.sort, str):
            raise ValueError('sort must be a string')

        if self.sort not in ('hot', 'new', 'rising', 'top', 'controversial'):
            raise ValueError('sort must be one of hot, new, rising, top, controversial')

        self.session.headers['User-Agent'] = extras.pop('user_agent', USER_AGENT)
        self.last: Optional[str] = None 
    
        limit: int = self.extras.pop('limit', 30)
        self.extras['limit'] = max(limit, 100)

    async def _fetch_many(self) -> List[RedditImage]:
        params: Dict[str, Any] = self.extras.copy()
        if self.last:
            params['after'] = self.last

        route = f'r/{self.subreddit}/{self.sort}/.json'
        data = await self.request(route, params=params)

        images: List[RedditImage] = []

        for child in data['data']['children']:
            post = child['data']
            if post['is_self']:
                continue
            
            url, name = post['url'], post['name']
            if post.get('is_gallery', False):
                images += await self._fetch_gallery_items(url, name)
            else:
                images.append(RedditImage(url, name))

            self.last = post['name']

        return images

    async def _fetch_gallery_items(self, url: str, name: str) -> List[RedditImage]:
        match = REDDIT_GALLERY_REGEX.match(url)
        if not match:
            if self.debug:
                print(f'{Colors.white}- {name}{Colors.reset}: {Colors.red}{url!r} is not a valid Reddit gallery URL. Skipping.{Colors.reset}')

            return []

        new_url = url.replace('gallery', 'comments') + '.json'
        async with self.session.get(new_url) as response:
            data = await response.json()

            images: List[RedditImage] = []

            medias = data[0]['data']['children'][0]['data']['media_metadata']
            for id, metadata in medias.items():
                if metadata['status'] != 'valid':
                    continue

                extension = metadata['m'].split('/')[-1]
                images.append(RedditImage(f'https://i.redd.it/{id}.{extension}', name))

            return images
        
        return []

    async def fetch_image(self, _: str = '') -> str:
        if not self._cache:
            # Cache the responses to avoid API calls
            self._cache = await self._fetch_many()

        image, name = self._cache.pop()
        self.last = name

        return image

    async def fetch_many(self, _: str = '') -> List[str]:
        images = await self._fetch_many()
        return [image.url for image in images]

    async def fetch_categories(self) -> Dict[str, int]:
        return {}
    