from typing import Dict, Type, Optional

from .abc import Provider
from .akaneko import AkanekoProvider
from .hmtai import HmtaiProvider
from .nekobot import NekobotProvider
from .waifupics import WaifupicsProvider
from .waifuim import WaifuimProvider
from .reddit import RedditProvider
from .danbooru import DanbooruProvider

ALL_PROVIDERS: Dict[str, Type[Provider]] = {
    'akaneko': AkanekoProvider,
    'nekobot': NekobotProvider,
    'hmtai': HmtaiProvider,
    'waifu.pics': WaifupicsProvider,
    'waifu.im': WaifuimProvider,
    'reddit': RedditProvider,
    'danbooru': DanbooruProvider,
}

def add_provider(name: str, provider: Type[Provider]):
    ALL_PROVIDERS[name] = provider

def get_provider(name: str) -> Optional[Type[Provider]]:
    return ALL_PROVIDERS.get(name)