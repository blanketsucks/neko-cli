from typing import Any, Dict, List

from abc import ABC, abstractmethod
import aiohttp

class Provider(ABC):
    BASE_URL: str

    def __init__(self, session: aiohttp.ClientSession, *, extras: Dict[str, Any], debug: bool = False):
        self.session = session
        self.extras = extras
        self.debug = debug

    @abstractmethod
    async def fetch_image(self, type: str) -> str:
        """
        Fetches an image from the provider with the given type.
        Optionally, subclasses may ignore the type argument.

        Arguments
        ---------
        type: :class:`str`
            The type of image to fetch.
        
        Returns
        -------
        :class:`str`
            The URL of the image.
        """
        raise NotImplementedError

    async def fetch_many(self, type: str) -> List[str]:
        """
        Fetches multiple images from the provider with the given type.
        Optionally, subclasses may ignore the type argument.

        The default implementation returns a single element list.
        This method should and is preferred to return a list of 30 elements.

        Arguments
        ---------
        type: :class:`str`
            The type of image to fetch.

        Returns
        -------
        :class:`list` of :class:`str`
            The URLs of the images.
        """
        return [await self.fetch_image(type)]

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
