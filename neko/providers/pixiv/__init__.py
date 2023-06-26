from typing import Dict, Any, List, Optional, Tuple

import re
import asyncio
import aiohttp
import logging
import datetime
import urllib.parse

from neko.providers.abc import Provider
from neko.providers.providers import register
from neko.utils import Colors

logger = logging.getLogger('neko')

URL = 'https://www.pixiv.net'
URL_REGEX = re.compile(r'https:\/\/www\.pixiv\.net\/en\/artworks\/(?P<id>\d+)')

IMAGE_URL = 'https://i.pximg.net/img-original/img/{year}/{month:02}/{day:02}/{hour:02}/{minute:02}/{second:02}/{id}_p{page}.{ext}'

class URLs:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.original: Optional[str] = data['original']

class Illustration:
    def __init__(self, session: aiohttp.ClientSession, illust: Dict[str, Any]):
        self._session = session

        self.id: str = illust['illustId']
        self.count: int = illust['pageCount']

        self.urls = URLs(illust['urls'])
        self.uploaded: datetime.datetime = datetime.datetime.fromisoformat(illust['uploadDate'])
        
    @property
    def is_nsfw(self) -> bool:
        return self.urls.original is None # If it doesn't have an original URL, it's most likely NSFW

@register('pixiv')
class PixivProvider(Provider):
    EXTRA_DOWNLOAD_HEADERS = {'Referer': URL}
    REQUIRES_EXTRAS: bool = True
    BASE_URL = URL

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any]):
        super().__init__(session, extras=extras)

        ids = extras.get('ids', [])
        if not isinstance(ids, list):
            raise TypeError('ids must be a list')
        
        self.ids: List[int] = []
        for id in ids:
            if not isinstance(id, (int, str)):
                raise TypeError('ids must be a list of integers or strings')
            
            if isinstance(id, int):
                self.ids.append(id)
                continue

            match = URL_REGEX.match(id)
            if match:
                self.ids.append(int(match['id']))
                continue

            try:
                self.ids.append(int(id))
            except ValueError:
                if self.debug:
                    print(f'{Colors.red}- {id!r} is not a valid ID.{Colors.reset}')

    async def is_valid_url(self, url: str) -> bool:
        try:
            async with self.session.get(url, headers={'Referer': URL}) as response:
                return response.status != 404
        except aiohttp.ClientError:
            await asyncio.sleep(1.5)
            return await self.is_valid_url(url)
        
    async def find_valid_url(self, uploaded: datetime.datetime, id: str, ext: str) -> Tuple[int, str]:
        tasks = [
            self.is_valid_url(
                IMAGE_URL.format(
                    year=uploaded.year, month=uploaded.month, day=uploaded.day, 
                    hour=uploaded.hour, minute=uploaded.minute, second=second, 
                    id=id, page=0, ext=ext
                )
            ) for second in range(60)
        ]

        results = await asyncio.gather(*tasks)
        for i, result in enumerate(results):
            if result:
                return (i, ext)
            
        if ext == 'png':
            return await self.find_valid_url(uploaded, id, 'jpg')

        return (-1, '')

    async def fetch_non_original_images(self, illust: Illustration) -> List[str]:
        images: List[str] = []

        # Get UTC+9 (Japan) timezone
        uploaded = illust.uploaded.astimezone(
            datetime.timezone(datetime.timedelta(hours=9))
        )

        ext = 'png'
        url = IMAGE_URL.format(
            year=uploaded.year, month=uploaded.month, day=uploaded.day, 
            hour=uploaded.hour, minute=uploaded.minute, second=uploaded.second, 
            id=illust.id, page=0, ext='png'
        )

        # From what I know, the preload data doesn't contain the correct timestamp
        # it's always missing the seconds which is necessary for the image URL
        # it also doesn't contain the extension, so we need to test both jpg and png

        try:
            second = uploaded.second
            if not await self.is_valid_url(url):
                url = url.replace('png', 'jpg'); ext = 'jpg'
                if not await self.is_valid_url(url):
                    (second, ext) = await self.find_valid_url(uploaded, illust.id, 'png')
        except Exception as exc:
            logger.error(f'Failed to fetch image: {exc!r}')
            return images

        for i in range(illust.count):
            images.append(IMAGE_URL.format(
                year=uploaded.year, month=uploaded.month, day=uploaded.day, 
                hour=uploaded.hour, minute=uploaded.minute, second=second, 
                id=illust.id, page=i, ext=ext
            ))

        return images
    
    async def fetch(self) -> List[str]:
        images: List[str] = []
        for id in self.ids:
            data = await self.request(f'/ajax/illust/{id}')
            if not data:
                logger.warning(f'Failed to fetch illustration {id}')
                continue
            
            illust = Illustration(self.session, data['body'])
            if not illust.urls.original:
                images.extend(await self.fetch_non_original_images(illust))
            else:
                images.extend([illust.urls.original.replace('_p0', f'_p{i}') for i in range(illust.count)])

        return images
        
    async def fetch_many(self, category: str) -> List[str]:
        return await self.fetch()

    async def fetch_image(self, category: str) -> str:
        return ''
    
    async def fetch_categories(self) -> Dict[str, str]:
        return {}
    
    def get_identifier_from_url(self, url: str) -> str:
        return urllib.parse.urlparse(url).path.split('/')[-1]
            