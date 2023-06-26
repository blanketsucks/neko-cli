from typing import Set, Any, Dict, TextIO

import aiohttp
import pathlib
import argparse
import asyncio
import toml
import json
import logging
import sys

from . import __version__
from .downloader import Downloader
from .providers import ALL_PROVIDERS, get_providers_that_require_extras
from .utils import Colors, chunk as _chunk, get_input
from .viewer import Application as ImageViewer
from .log import create_logger

REQUIRE_EXTRAS = get_providers_that_require_extras()

class State:
    def __init__(self, downloader: Downloader, logger: logging.Logger) -> None:
        self.downloader = downloader
        self.logger = logger

        self.successful = 0

        self.lock = asyncio.Lock()

    async def download(self, url: str, *, depth: int = 0) -> None:
        try:
            is_successful = await self.downloader.download(url)
            async with self.lock:
                self.successful += is_successful

            if not is_successful:
                if depth == 5:
                    self.logger.error('Failed to download %r', url)
                    return
                
                return await self.download(url, depth=depth + 1)
        except Exception as e:
            if depth == 5:
                self.logger.exception('Failed to download %r', url, exc_info=e)
                return

            return await self.download(url, depth=depth + 1)
        
async def download(urls: Set[str], downloader: Downloader, logger: logging.Logger, amount: int) -> None:
    state = State(downloader, logger)
    for chunk in _chunk(urls, 50):
        await asyncio.gather(*[state.download(url) for url in chunk])

    print(f'\n{Colors.white}- Successfully downloaded {state.successful}/{amount} images.{Colors.reset}\n')
    await downloader.session.close()

def parse_extras(file: TextIO, provider: str) -> Dict[str, Any]:
    path = pathlib.Path(file.name).resolve()
    if path.suffix == '.json':
        return json.load(file)
    elif path.suffix != '.toml':
        print(f'{Colors.red}- Invalid file extension {path.suffix!r}. Supported file extensions are \'.json\' and \'.toml\'{Colors.reset}')
        sys.exit(1)
    
    data = toml.load(file)['provider']
    extras = data.get(provider, {})

    if not extras and provider in REQUIRE_EXTRAS:
        print(f'{Colors.red}- Provider {provider!r} not found in {path.name!r}.{Colors.reset}')
        sys.exit(1)

    return extras

async def main(args: argparse.Namespace) -> int:
    logger = create_logger()

    if not args.debug:
        logger.setLevel(logging.ERROR)

    if args.extras is not None:
        with args.extras as file:
            args.extras = parse_extras(file, args.provider)
    else:
        args.extras = {}

    args.extras['nsfw'] = args.nsfw

    if args.max_retries.lower() == 'none':
        args.max_retries = float('inf')
    elif args.max_retries.isdigit():
        args.max_retries = int(args.max_retries)
    else:
        print(f'{Colors.red}- Invalid argument for --max-retries')
        return 1

    session = aiohttp.ClientSession()
    provider = ALL_PROVIDERS[args.provider](session, extras=args.extras)

    logger.info('Using provider %r.', args.provider)

    categories = await provider.fetch_categories()
    if args.category is None and categories:
        args.category = get_input('{white}- Please enter the category you want to download (You can also type `check` to see all the available categories){reset}: {green}')
        print(Colors.reset.value, end='')
        
        if args.category in ('q', 'quit', 'exit'):
            await session.close()

            return 0

    if args.category == 'check':
        print()
        if not categories:
            print(f'{Colors.white}- There are no categories available with this provider.{Colors.reset}')
        else:
            for key, value in categories.items():
                if value < 0:
                    fmt = f'{Colors.white}- {key.title()}{Colors.reset}'
                else:
                    fmt = f'{Colors.white}- {key.title()}{Colors.reset}: {Colors.green}{value}{Colors.reset}'

                print(fmt)

        await session.close()
        return 0

    if categories and args.category not in categories:
        print(f'\n{Colors.red}- Invalid category.{Colors.reset}')

        await session.close()
        return 1

    path = pathlib.Path(args.path).resolve()
    path.mkdir(parents=True, exist_ok=True)

    fetched = 0
    retries = 0

    if args.amount == 'all':
        args.amount = categories[args.category]
        if args.amount < 0:
            print(f'{Colors.red}- Sorry but `all` is not supported with this provider.{Colors.reset}')
            await session.close()

            return 1
    else:
        if args.provider in ('pixiv', 'nhentai'):
            args.amount = len(args.extras['ids'])
        else:
            args.amount = int(args.amount)

    print()

    downloader = Downloader(provider, path, headers=provider.EXTRA_DOWNLOAD_HEADERS)

    all_urls: Set[str] = set()
    for file in path.iterdir():
        if file.suffix == '.tmp':
            file.unlink() # Remove any temporary files that might be left over from a previous run.

    if args.provider in ('pixiv', 'nhentai'):
        urls = await provider.fetch_many(args.category)
        fetched += len(urls)

        for url in urls:
            p = await downloader.fetch_download_path(url)
            if p.exists():
                logger.info('%r already exists. Ignoring.', p.name)
                continue

            all_urls.add(url)

        provider.finalize()
        await download(all_urls, downloader, logger, args.amount)

        if args.view:
            viewer = ImageViewer(paths=[], debug=args.debug)
            viewer.images = viewer.load_images([path])

            viewer.run()

        return 0

    while fetched <= args.amount:
        if args.amount >= 30 and (args.amount - fetched) >= 30:
            urls = await provider.fetch_many(args.category)
        else:
            urls = [await provider.fetch_image(args.category)]

        if not urls:
            break
        
        for url in urls:
            try:
                p = await downloader.fetch_download_path(url)
            except KeyError:
                logger.warning('Invalid URL %r. Ignoring.', url)
                continue

            if p.exists():
                logger.info('%r already exists. Ignoring.', p.name)

                if not args.retry_if_exists:
                    fetched += 1; continue
                elif retries < args.max_retries:
                    retries += 1; continue

                logger.error('Reached maximum amount of consecutive retries.')

                provider.finalize()
                await session.close()

                return 1
            else:
                all_urls.add(url)
                fetched += 1

    provider.finalize()
    await download(all_urls, downloader, logger, args.amount)

    if args.view:
        viewer = ImageViewer(paths=[str(path)], debug=args.debug)
        viewer.run()

    return 0
