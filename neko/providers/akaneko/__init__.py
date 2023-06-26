from typing import Dict

import re
import hashlib
import urllib.parse

from neko.providers.abc import Provider
from neko.providers.providers import register

AKANEKO_CATEGORIES = (
    'ass', 'bdsm', 'bondage', 'cum', 'hentai', 'femdom',
    'doujin', 'maid', 'maids', 'orgy', 'panties', 'nsfwwallpapers',
    'nsfwmobilewallpapers', 'netorare', 'gifs', 'gif', 'blowjob',
    'feet', 'pussy', 'uglybastard', 'uniform', 'gangbang', 'foxgirl',
    'cumslut', 'glasses', 'thighs', 'tentacles', 'masturbation',
    'school', 'yuri', 'zettaiRyouiki', 'succubus', 'neko',
    'sfwfoxes', 'wallpapers', 'mobilewallpapers'
)

MEDIA_DISCORD_REGEX = re.compile(r'https:\/\/media\.discordapp\.net\/attachments\/(?P<channel_id>\d+)\/(?P<message_id>\d+)\/(?P<filename>[^?]*)')

@register('akaneko')
class AkanekoProvider(Provider):
    BASE_URL = 'https://akaneko-api.herokuapp.com/api/'

    async def fetch_image(self, type: str) -> str:
        data = await self.request(type)
        return data['url']

    async def fetch_categories(self) -> Dict[str, int]:
        return {category: -1 for category in AKANEKO_CATEGORIES}

    def get_identifier_from_url(self, url: str) -> str:
        match = MEDIA_DISCORD_REGEX.match(url)
        if match:
            ident = '/'.join(value for value in match.groupdict().values())
            return hashlib.md5(ident.encode()).hexdigest()

        parsed = urllib.parse.urlparse(url)

        split = parsed.path.split('/')
        if len(split) <= 2:
            return split[-1]

        return parsed.path.split('/')[2]
        