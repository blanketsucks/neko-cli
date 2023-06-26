from typing import Any, Dict, List

import aiohttp
import logging
import re

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.common.exceptions import TimeoutException
except ImportError:
    uc, WebDriverWait, TimeoutException = None, None, None

from neko.providers.abc import Provider
from neko.providers.providers import register
from neko import utils

logger = logging.getLogger('neko')

URL_REGEX = re.compile(r'https:\/\/nhentai\.net\/g\/(?P<id>\d+)/?')
IMAGE_URL_REGEX = re.compile(r'https:\/\/(\w{2})\.nhentai\.net\/galleries\/(?P<id>\d+)\/(?P<page>\d+)\.(?P<ext>jpg|png)')

@register('nhentai')
class NHentaiProvider(Provider):
    BASE_URL = 'https://nhentai.net'
    REQUIRES_EXTRAS = True

    DEFAULT_TIMEOUT = 120.0

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any]):
        if not uc or not WebDriverWait:
            raise RuntimeError('You need to install undetected_chromedriver to use this provider.')

        super().__init__(session, extras=extras)

        self.ids: List[int] = []
        for id in extras.get('ids', []):
            if isinstance(id, int):
                self.ids.append(id)
                continue

            match = URL_REGEX.match(id)
            if match:
                self.ids.append(int(match.group('id')))
                continue

            try:
                self.ids.append(int(id))
            except ValueError:
                pass

        self.timeout = extras.get('timeout', self.DEFAULT_TIMEOUT)
        self.driver = uc.Chrome(headless=True)

    def finalize(self) -> None:
        self.driver.close()
        self.driver.quit()

    def fetch(self, id: int) -> List[str]:
        self.driver.get(f'https://nhentai.net/g/{id}')

        try:
            elements = WebDriverWait(self.driver, self.timeout).until(       # type: ignore
                lambda driver: driver.find_elements(uc.By.CLASS_NAME, 'lazyload') # type: ignore
            )
        except TimeoutException:
            logger.warning('Timed out while fetching doujin %d.', id)
            return []

        images = [element.get_attribute('data-src') for element in elements][1:-5]
        return[
            re.sub(r'(\w{2})\.nhentai\.net', r'i5.nhentai.net', image.replace('t.', '.'))
            for image in images
        ]
        
    async def fetch_many(self, category: str) -> List[str]:
        images = []
        for id in self.ids:
            logger.info('Fetching doujin %d.', id)
            images.extend(await utils.to_thread(self.fetch, id))

        return images

    async def fetch_image(self, category: str) -> str:
        return ''
    
    async def fetch_categories(self) -> Dict[str, int]:
        return {}
    
    def get_identifier_from_url(self, url: str) -> str:
        match = IMAGE_URL_REGEX.match(url)
        assert match

        return f'{match.group("id")}_{match.group("page")}.{match.group("ext")}'