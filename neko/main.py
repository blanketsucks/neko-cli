import aiohttp
import pathlib
import argparse
import asyncio
import json

from .downloader import Downloader
from .providers import ALL_PROVIDERS
from .utils import Colors, get_input
from .viewer import Application as ImageViewer

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='neko-cli', description='Download NSFW and SFW from various providers.')

    parser.add_argument('-t', '--type', type=str, help='The category to download.', required=False)
    parser.add_argument('-a', '--amount', type=str, help='The amount of images to download.', required=False)
    parser.add_argument('-p', '--path', type=str, help='The path where to save the images. Defaults to `./images`', default='./images')
    parser.add_argument('--provider', type=str, help='The provider to use. Defaults to `nekobot`.', default='nekobot', choices=ALL_PROVIDERS.keys())
    parser.add_argument('--retry-if-exists', action='store_true', help='Retry the request if the file already exists. Defaults to False', default=False)
    parser.add_argument('--max-retries', type=str, help='The maximum amount of consecutive retries or `none`. Defaults to `none`', default='none')
    parser.add_argument('--extras', type=argparse.FileType('r'), help='''
    Extra arguments to be passed to the provider. Should be a file path to a JSON file.
    Currently the only provider that uses this information is reddit.
    ''', required=False)
    parser.add_argument('--view', action='store_true', help='View the images after downloading.')
    parser.add_argument('--debug', action='store_true', help='Print debug information.')

    return parser

async def main():
    parser = create_argument_parser()
    args = parser.parse_args()

    if args.extras is not None:
        with args.extras as file:
            args.extras = json.load(file)
    else:
        args.extras = {}

    if args.max_retries.lower() == 'none':
        args.max_retries = float('inf')
    elif args.max_retries.isdigit():
        args.max_retries = int(args.max_retries)
    else:
        print(f'{Colors.red}- Invalid argument for --max-retries')
        return 1

    session = aiohttp.ClientSession()
    provider = ALL_PROVIDERS[args.provider](session, extras=args.extras, debug=args.debug)

    if args.debug:
        print(f'{Colors.white}- Provider used{Colors.reset}: {Colors.green}{args.provider!r}{Colors.reset}\n')

    categories = await provider.fetch_categories()
    if args.type is None and categories:
        args.type = get_input('{white}- Please enter the category you want to download (You can also type `check` to see all the available categories){reset}: {green}')
        if args.type in ('q', 'quit', 'exit'):
            print(Colors.reset.value)

            await session.close()
            return 0

    if args.type == 'check':
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

    if categories and args.type not in categories:
        print(f'{Colors.red}- Invalid category.{Colors.reset}')
        await session.close()

        return 1

    path = pathlib.Path(args.path).resolve()
    if not path.exists():
        path.mkdir()

    if args.amount is None:
        args.amount = get_input('{white}- Please enter the amount of images you want to download (You can also type `all` to download all the images){reset}: {green}')
        if args.amount in ('q', 'quit', 'exit'):
            print(Colors.reset.value)

            await session.close()
            return 0

    i = 0
    success = 0
    retries = 0

    if args.amount == 'all':
        args.amount = categories[args.type]
        if args.amount < 0:
            print(f'{Colors.red}- Sorry but `all` is not supported with this provider.{Colors.reset}')
            await session.close()

            return 1
    else:
        args.amount = int(args.amount)

    print()
    
    async def _download(url: str) -> None:
        nonlocal success, i, retries

        downloader = Downloader(session, url, path, debug=args.debug)

        identifier = provider.get_identifier_from_url(url)
        p = await downloader.fetch_download_path(identifier)
        if p.exists():
            if args.debug:
                fmt = f'{Colors.white}- {p.name}{Colors.reset}: {Colors.green}Already downloaded. Ignoring.{Colors.reset}'
                print(fmt)

            if not args.retry_if_exists:
                i += 1
            else:
                if retries < args.max_retries:
                    retries += 1
                else:
                    fmt = f'{Colors.red}- Reached maximum amount of consecutive retries.{Colors.reset}'
                    print(fmt)

                    await session.close()
                    exit(1)
        else:
            success += await downloader.download(identifier)

            retries = 0
            i += 1

    while True:
        if i == args.amount:
            break
        
        if args.amount >= 30 and (args.amount - i) >= 30:
            urls = await provider.fetch_many(args.type)
        else:
            urls = [await provider.fetch_image(args.type)]

        for url in urls:
            await _download(url)

        await asyncio.sleep(0.5)
    
    print(f'\n{Colors.white}- Successfully downloaded {success}/{args.amount} images.{Colors.reset}\n')
    await session.close()

    if args.view:
        viewer = ImageViewer(paths=[])
        viewer.images = viewer.load_images([path])

        viewer.run()

    return 0
