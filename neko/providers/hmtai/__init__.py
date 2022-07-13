from typing import Dict

import hashlib
import re

from neko.providers.abc import Provider

DISCORD_CDN_REGEX = re.compile(r'https:\/\/cdn\.discordapp\.com\/attachments\/(?P<channel_id>\d+)\/(?P<message_id>\d+)\/(?P<filename>[^?]*)')

class HmtaiProvider(Provider):
    BASE_URL = 'https://hmtai.herokuapp.com/v2/'

    async def fetch_image(self, type: str) -> str:
        async with self.session.get(self.BASE_URL + type) as response:
            data = await response.json()
            return data['url']

    async def fetch_categories(self) -> Dict[str, int]:
        async with self.session.get(self.BASE_URL + 'endpoints') as response:
            data = await response.json()
            categories: Dict[str, int] = {}

            categories.update({category: -1 for category in data['sfw']})
            categories.update({category: -1 for category in data['nsfw']})

            return categories

    def get_identifier_from_url(self, url: str) -> str:
        match = DISCORD_CDN_REGEX.match(url)
        assert match, 'Invalid URL'

        ident = '/'.join(value for value in match.groupdict().values())
        return hashlib.md5(ident.encode()).hexdigest()