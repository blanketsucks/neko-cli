import asyncio
import argparse

from . import __version__
from .main import main as amain
from .providers import ALL_PROVIDERS

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='neko-cli', description='Download NSFW and SFW from various providers.'
    )

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
        required=False,
        default='0'
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
        help='The provider to use.', 
        required=False,
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
        help='Extra arguments to be passed to the provider. Should be a file path to a JSON/TOML file.', 
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

def main() -> int:
    parser = create_argument_parser()

    try:
        return asyncio.run(amain(parser.parse_args()))
    except KeyboardInterrupt:
        return 1

if __name__ == '__main__':
    exit(main())