import traceback
import aiohttp
import pathlib
import argparse
import asyncio
import json

from . import __version__

from .downloader import Downloader, VALID_EXTENSIONS
from .providers import ALL_PROVIDERS
from .utils import Colors, get_input
from .viewer import Application as ImageViewer

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='neko-cli', description='Download NSFW and SFW from various providers.')

    parser.add_argument(
        '-c', 
        '--category', 
        type=str, 
        help='The category to download.', 
        required=False
    )

    parser.add_argument(
        '-a', 
        '--amount', 
        type=str, 
        help='The amount of images to download.', 
        required=False
    )

    parser.add_argument(
        '-p', 
        '--path', 
        type=str, 
        help='The path where to save the images. Defaults to `./images`.', 
        default='./images'
    )

    parser.add_argument(
        '--provider', 
        type=str, 
        help='The provider to use. Defaults to `nekobot`.', 
        default='nekobot', 
        choices=ALL_PROVIDERS.keys()
    )

    parser.add_argument(
        '--retry-if-exists', 
        action='store_true', 
        help='Retry the request if the file already exists. Defaults to False.', 
        default=False
    )

    parser.add_argument(
        '--max-retries', 
        type=str, 
        help='The maximum amount of consecutive retries or `none`. Defaults to `none`.', 
        default='none'
    )

    parser.add_argument(
        '--extras', 
        type=argparse.FileType('r'), 
        help='Extra arguments to be passed to the provider. Should be a file path to a JSON file.', 
        required=False
    )

    parser.add_argument(
        '--nsfw', 
        action='store_true', 
        help='Download NSFW images. Only matters with waifu.im and waifu.pics. Defaults to False', 
        default=False
    )

    parser.add_argument('--view', action='store_true', help='View the images after downloading.')
    parser.add_argument('--debug', action='store_true', help='Print debug information.')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    return parser

async def main():
    parser = create_argument_parser()
    args = parser.parse_args()

    if args.extras is not None:
        with args.extras as file:
            args.extras = json.load(file)
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
    provider = ALL_PROVIDERS[args.provider](session, extras=args.extras, debug=args.debug)

    if args.debug:
        print(f'{Colors.white}- Provider used{Colors.reset}: {Colors.green}{args.provider!r}{Colors.reset}\n')

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
    if not path.exists():
        path.mkdir()

    if args.amount is None:
        args.amount = get_input('{white}- Please enter the amount of images you want to download (You can also type `all` to download all the images){reset}: {green}')
        print(Colors.reset.value, end='')
        
        if args.amount in ('q', 'quit', 'exit'):
            await session.close()
            return 0

    i = 0
    success = 0
    retries = 0

    if args.amount == 'all':
        args.amount = categories[args.category]
        if args.amount < 0:
            print(f'{Colors.red}- Sorry but `all` is not supported with this provider.{Colors.reset}')
            await session.close()

            return 1
    else:
        args.amount = int(args.amount)

    print()

    downloader = Downloader(provider, path, debug=args.debug)
    while True:
        if i == args.amount:
            break
        
        if args.amount >= 30 and (args.amount - i) >= 30:
            urls = await provider.fetch_many(args.category)
        else:
            urls = [await provider.fetch_image(args.category)]

        for url in urls:
            headers = await downloader.fetch_headers(url)
            identifier = provider.get_identifier_from_url(url)

            extension = downloader.get_file_extension(identifier, headers)
            if extension not in VALID_EXTENSIONS:
                if downloader.debug:
                    fmt = f"{Colors.white}- {identifier}{Colors.reset}: {Colors.red}Unsupported file type '{extension}'.{Colors.reset}"
                    print(fmt)

                continue

            p = await downloader.fetch_download_path(url)
            if p.exists():
                if args.debug:
                    fmt = f'{Colors.white}- {p.name}{Colors.reset}: {Colors.green}Already downloaded. Ignoring.{Colors.reset}'
                    print(fmt)

                if not args.retry_if_exists:
                    i += 1
                else:
                    if retries < args.max_retries:
                        retries += 1
                        continue

                    print(f'{Colors.red}- Reached maximum amount of consecutive retries.{Colors.reset}')

                    await session.close()
                    return 1
            else:
                success += await downloader.download(url); i += 1; retries = 0
            
        await asyncio.sleep(0.5)
    
    print(f'\n{Colors.white}- Successfully downloaded {success}/{args.amount} images.{Colors.reset}\n')
    await session.close()

    if args.view:
        viewer = ImageViewer(paths=[])
        viewer.images = viewer.load_images([path])

        viewer.run()

    return 0
