# neko-cli

A CLI tool written in Python to view and download images across various APIs.

## Installation

**Python3.8 or higher is required.**

Currently installation is only available via git.

```bash
# Windows
py -3 -m pip install git+https://github.com/blanketsucks/neko.git

# Linux or MacOS
python3 -m pip install git+https://github.com/blanketsucks/neko.git
```

## Usage

```bash
usage: neko-cli [-h] [-c CATEGORY] [-a AMOUNT] [-p PATH] [--provider {akaneko,nekobot,hmtai,waifu.pics,waifu.im,reddit,danbooru}]
                [--retry-if-exists] [--max-retries MAX_RETRIES] [--extras EXTRAS] [--view] [--debug] [--version]

Download NSFW and SFW from various providers.

optional arguments:
  -h, --help            show this help message and exit
  -c CATEGORY, --category CATEGORY
                        The category to download.
  -a AMOUNT, --amount AMOUNT
                        The amount of images to download.
  -p PATH, --path PATH  The path where to save the images. Defaults to `./images`.
  --provider {akaneko,nekobot,hmtai,waifu.pics,waifu.im,reddit,danbooru}
                        The provider to use. Defaults to `nekobot`.
  --retry-if-exists     Retry the request if the file already exists. Defaults to False.
  --max-retries MAX_RETRIES
                        The maximum amount of consecutive retries or `none`. Defaults to `none`.
  --extras EXTRAS       Extra arguments to be passed to the provider. Should be a file path to a JSON file.
  --view                View the images after downloading.
  --debug               Print debug information.
  --version             show program's version number and exit
```

The library also provides a tool for viewing files which is based on `tkinter`

```bash
usage: neko-viewer [-h] [--path PATH] [--width WIDTH] [--height HEIGHT] [--debug]

An Image viewer.

optional arguments:
  -h, --help       show this help message and exit
  --path PATH      Path to the directory containing the images.
  --width WIDTH    Width of the window. Defaults to 720. Images are resized according to this argument.
  --height HEIGHT  Height of the window. Defaults to 720. Images are resized according to this argument.
  --debug          Print debug messages
```

## Library Usage

Examples can be found in the [`examples`](https://github.com/blanketsucks/neko/tree/master/examples) directory.

Note that when importing the library, you would need to import `neko`.