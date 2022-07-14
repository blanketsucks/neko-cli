from typing import Any, Dict, List

from neko.providers.abc import Provider

class WaifuimProvider(Provider):
    BASE_URL = 'https://api.waifu.im/'

    async def request(self, type: str, **params: Any) -> Dict[str, Any]:
        params['selected_tags'] = type
        params['nsfw'] = 'on'

        return await super().request('random', params=params)

    async def fetch_image(self, type: str) -> str:
        data = await self.request(type)
        return data['images'][0]['url']

    async def fetch_many(self, type: str) -> List[str]:
        data = await self.request(type, many='true')
        return [image['url'] for image in data['images']]

    async def fetch_categories(self) -> Dict[str, int]:
        data = await self.request('tags', params={'full': 'on'})
        return {tag['name']: -1 for tag in data['nsfw']}
