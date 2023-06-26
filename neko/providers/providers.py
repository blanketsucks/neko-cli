from typing import Callable, Dict, Type, Optional, TypeVar

from .abc import Provider

ALL_PROVIDERS: Dict[str, Type[Provider]] = {}

T = TypeVar('T', bound=Provider)

def register(name: str) -> Callable[[Type[T]], Type[T]]:
    def wrapper(cls: Type[T]):
        add_provider(name, cls)
        return cls

    return wrapper

def add_provider(name: str, provider: Type[Provider]):
    ALL_PROVIDERS[name] = provider

def get_provider(name: str) -> Optional[Type[Provider]]:
    return ALL_PROVIDERS.get(name)

def get_providers_that_require_extras() -> Dict[str, Type[Provider]]:
    return {name: provider for name, provider in ALL_PROVIDERS.items() if provider.REQUIRES_EXTRAS}