from typing import Any, Dict, List

from neko.providers.abc import Provider

class WaifuimProvider(Provider):
    BASE_URL = 'https://api.waifu.im/'

    async def request(self, type: str, **params: Any) -> Dict[str, Any]:
        params['selected_tags'] = type
        params['nsfw'] = 'on'

        async with self.session.get(self.BASE_URL + 'random', params=params) as response:
            return await response.json()

    async def fetch_image(self, type: str) -> str:
        data = await self.request(type)
        return data['images'][0]['url']

    async def fetch_many(self, type: str) -> List[str]:
        data = await self.request(type, many='true')
        return [image['url'] for image in data['images']]

    async def fetch_categories(self) -> Dict[str, int]:
        async with self.session.get(self.BASE_URL + 'tags', params={'full': 'on'}) as response:
            data = await response.json()
            return {tag['name']: -1 for tag in data['nsfw']}
