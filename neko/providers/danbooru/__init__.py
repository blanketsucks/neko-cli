from typing import Dict, Any, List, Optional, NamedTuple

import aiohttp

from neko.providers.abc import Provider
from neko.providers.utils import get_str_value

REQUEST_ROUTES: Dict[str, str] = {
    'popular': 'explore/posts/popular.json',
    'curated': 'explore/posts/curated.json',
    'viewed': 'explore/posts/viewed.json',
    'random': 'posts/random.json',
}

RATINGS: Dict[str, str] = {
    'safe': 's',
    'questionable': 'q',
    'explicit': 'e',
}

class DanbooruFile(NamedTuple):
    extension: str
    size: int
    url: str

class DanbooruImage(NamedTuple):
    md5: str
    source: str
    file: DanbooruFile
    tags: List[str]

class DanbooruProvider(Provider):
    BASE_URL = 'https://danbooru.donmai.us/'

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any], debug: bool = False):
        super().__init__(session, extras=extras, debug=debug)

        self.params: Dict[str, Any] = {}

        self.username = get_str_value(extras, 'username')
        self.api_key = get_str_value(extras, 'api_key')
        self.rating: Optional[str] = extras.pop('rating', None)
        self.limit: int = min(extras.pop('limit', 30), 200)

        sort = extras.pop('sort', None)
        self.sort_by: Optional[str] = None

        if sort is not None:
            if not isinstance(sort, dict):
                raise ValueError('sort must be a dict')

            self.sort_by = get_str_value(sort, 'by')
            if self.sort_by not in ('popular', 'curated', 'random', 'viewed'):
                raise ValueError('sort.by must be one of popular, curated, random, viewed')

            scale = sort.pop('scale', None)
            if scale is not None:
                if not isinstance(scale, str):
                    raise ValueError('sort.scale must be a string')

                if scale not in ('day', 'week', 'month'):
                    raise ValueError('sort.scale must be one of day, week, month')

                self.params['scale'] = scale

            date = sort.pop('date', None)
            if date is not None:
                if not isinstance(date, str):
                    raise ValueError('sort.date must be a string')

                self.params['date'] = date

        tags: List[str] = extras.pop('tags', [])
        if self.rating is not None:
            if self.rating not in RATINGS:
                raise ValueError('rating must be one of safe, questionable, explicit')

            tags.append(f'rating:{RATINGS[self.rating]}')

        self.params['limit'] = self.limit
        self.params['tags'] = ' '.join(tags)
 
        self.auth = aiohttp.BasicAuth(self.username, self.api_key)

        self._cache: List[DanbooruImage] = []

    @property
    def tags(self) -> List[str]:
        return self.params['tags'].split(' ')

    @tags.setter
    def tags(self, tags: List[str]) -> None:
        self.params['tags'] = ' '.join(tags)

    async def _fetch_many(self) -> List[DanbooruImage]:
        route = self.get_request_route()
        payload: List[Dict[str, Any]] = await self.request(route, **self.params)

        images: List[DanbooruImage] = []

        for data in payload:
            file = DanbooruFile(extension=data['file_ext'], size=data['file_size'], url=data['file_url'])
            image = DanbooruImage(md5=data['md5'], source=data['source'], file=file, tags=data['tag_string_general'].split(' '))

            images.append(image)

        return images

    def get_cached_images(self) -> List[DanbooruImage]:
        return self._cache.copy()

    async def request(self, route: str, **params: Any) -> Any:
        return await super().request(route, auth=self.auth, params=params)

    def get_request_route(self) -> str:
        return REQUEST_ROUTES.get(self.sort_by, 'posts.json') # type: ignore

    async def fetch_image(self, _: str = '') -> str:
        if not self._cache:
            self._cache = await self._fetch_many()

        image = self._cache.pop()
        return image.file.url

    async def fetch_many(self, _: str = '') -> List[str]:
        images = await self._fetch_many()
        return [image.file.url for image in images]

    async def fetch_categories(self) -> Dict[str, int]:
        return {}