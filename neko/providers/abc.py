from typing import Any, Dict, List, Optional

from abc import ABC, abstractmethod
import aiohttp
import asyncio

from neko.utils import Colors

class Provider(ABC):
    BASE_URL: str

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any], debug: bool = False):
        self.session = session
        self.extras = extras
        self.debug = debug

    async def request(self, route: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Requests the given route with the given kwargs.

        Arguments
        ---------
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
        async with self.session.request(url, **kwargs) as response:
            if response.status == 429:
                retry_after = float(response.headers['Retry-After'])

                if self.debug:
                    print(f'{Colors.red}- Too many requests. Retrying in {retry_after} seconds.{Colors.reset}')

                await asyncio.sleep(retry_after)
                return await self.request(route, **kwargs)

            return await response.json()

        return {}

    @abstractmethod
    async def fetch_image(self, category: str) -> str:
        """
        Fetches an image from the provider with the given category.
        Optionally, subclasses may ignore the type argument.

        Arguments
        ---------
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

        The default implementation returns a single element list.
        This method should and is preferred to return a list of 30 elements.

        Arguments
        ---------
        category: :class:`str`
            The category of image to fetch.

        Returns
        -------
        :class:`list` of :class:`str`
            The URLs of the images.
        """
        return [await self.fetch_image(category)]

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

        Arguments
        ---------
        url: :class:`str`
            The URL of the image.

        Returns
        -------
        :class:`str`
            The identifier of the image.
        """
        return url.split('/')[-1]
