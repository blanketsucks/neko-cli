from typing import Any, Dict, Generic, List, Optional, TypeVar

from abc import ABC, abstractmethod
import aiohttp
import logging
import asyncio

from neko.utils import Colors

logger = logging.getLogger('neko')

T = TypeVar('T')

class Provider(ABC):
    EXTRA_DOWNLOAD_HEADERS: Dict[str, str] = {}
    REQUIRES_EXTRAS: bool = False
    BASE_URL: str

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any]):
        self.session = session
        self.extras = extras

    def finalize(self) -> None:
        return 

    async def request(self, route: Optional[str] = None, **kwargs: Any) -> Any:
        """
        Requests the given route with the given kwargs.

        Parameters
        -----------
        route: Optional[:class:`str`]
            The route to request.
        **kwargs: Any
            Extra arguments to pass to the request.

        Returns
        -------
        :class:`dict`
            The JSON response.
        """
        if route is None:
            url = self.BASE_URL
        else:
            url = self.BASE_URL + route

        kwargs.setdefault('method', 'GET')
        async with self.session.request(url=url, **kwargs) as response: # type: ignore
            if response.status == 429:
                try:
                    retry_after = float(response.headers['Retry-After'])
                except KeyError:
                    retry_after = 60.0

                logger.error('%r: Too many requests. Retrying in %f seconds.', url, retry_after)

                await asyncio.sleep(retry_after)
                return await self.request(route, **kwargs)

            if response.status != 200:
                logger.error('%r: %d %s', url, response.status, response.reason)
                return {}

            return await response.json()

        return {}

    @abstractmethod
    async def fetch_image(self, category: str) -> str:
        """
        Fetches an image from the provider with the given category.
        Optionally, subclasses may ignore the type argument.

        Parameters
        -----------
        category: :class:`str`
            The category of image to fetch.
        
        Returns
        -------
        :class:`str`
            The URL of the image.
        """
        raise NotImplementedError

    async def fetch_many(self, category: str) -> List[str]:
        """
        Fetches multiple images from the provider with the given category.
        Optionally, subclasses may ignore the type argument.

        Parameters
        -----------
        category: :class:`str`
            The category of image to fetch.

        Returns
        -------
        :class:`list` of :class:`str`
            The URLs of the images.
        """
        images: List[str] = []
        for _ in range(30):
            image = await self.fetch_image(category)
            images.append(image)

        return images

    @abstractmethod
    async def fetch_categories(self) -> Dict[str, int]:
        """
        Fetches the categories of the provider.

        Returns
        -------
        :class:`dict`
            The categories of the provider.
        """
        raise NotImplementedError

    def get_identifier_from_url(self, url: str) -> str:
        """
        Returns the identifier of the image from the given URL.
        The identifier returned must be unique.

        Parameters
        -----------
        url: :class:`str`
            The URL of the image.

        Returns
        -------
        :class:`str`
            The identifier of the image.
        """
        return url.split('/')[-1]

class CachableProvider(Provider, Generic[T]):
    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any]):
        super().__init__(session, extras=extras)
        self._cache: List[T] = []

    def get_cached_images(self) -> List[T]:
        return self._cache.copy()
