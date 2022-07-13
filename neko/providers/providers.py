from typing import Dict, Type

from .abc import Provider

from .akaneko import AkanekoProvider
from .hmtai import HmtaiProvider
from .nekobot import NekobotProvider
from .waifupics import WaifupicsProvider
from .waifuim import WaifuimProvider
from .reddit import RedditProvider

ALL_PROVIDERS: Dict[str, Type[Provider]] = {
    'akaneko': AkanekoProvider,
    'nekobot': NekobotProvider,
    'hmtai': HmtaiProvider,
    'waifu.pics': WaifupicsProvider,
    'waifu.im': WaifuimProvider,
    'reddit': RedditProvider,
}

def add_provider(name: str, provider: Type[Provider]):
    ALL_PROVIDERS[name] = provider