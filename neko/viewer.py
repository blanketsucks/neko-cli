from __future__ import annotations

from typing import Any, List, Optional, Tuple

from PIL import Image, ImageTk, UnidentifiedImageError, ImageSequence
from tkinter import simpledialog
from itertools import count
from enum import Enum
import argparse
import logging
import random
import tkinter
import pathlib
import math

class Colors(str, Enum):
    red = '\u001b[1;31m'
    green = '\u001b[1;32m'
    yellow = '\u001b[1;33m'
    white = '\u001b[1;37m'
    reset = '\u001b[0m'

class ColorFormatter(logging.Formatter):
    LEVELS: List[Tuple[int, Colors]] = [
        (logging.INFO, Colors.green),
        (logging.WARNING, Colors.yellow),
        (logging.ERROR, Colors.red),
        (logging.CRITICAL, Colors.red)
    ]

    FORMATS = {
        level: logging.Formatter(f'{color}[%(levelname)s]{Colors.reset} %(message)s')
        for level, color in LEVELS
    }

    def format(self, record: logging.LogRecord):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.INFO]

        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'{Colors.red}{text}{Colors.reset}'

        output = formatter.format(record)
        record.exc_text = None

        return output

def create_logger():
    logger = logging.getLogger('neko.viewer')
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter())

    logger.addHandler(handler)
    return logger

logger = create_logger()

def _sort(image: str) -> Any:
    image, _ = image.split('.')
    if '_' in image:
        image, page = image.split('_')
        if 'p' in page:
            _, page = page.split('p')
            print(page)

        return int(image) if image.isdigit() else image, int(page) if page.isdigit() else page

    if not image.isdigit():
        return (image, 0)
    
    return (int(image), 0)

# From https://stackoverflow.com/a/43770948
class ImageLabel(tkinter.Label):
    def load(self, image: Image.Image, width: int, height: int):
        self.location = 0
        self.frames: List[ImageTk.PhotoImage] = []
        self.width = width
        self.height = height
        self.after_id: Optional[str] = None

        try:
            for frame in count(1):
                self.frames.append(ImageTk.PhotoImage(image.copy()))
                image.seek(frame)
        except EOFError:
            pass

        self.delay = image.info.get('duration', 100)
        if len(self.frames) == 1:
            self.config(image=self.frames[0], width=width, height=height, anchor='center')
        else:
            self.next_frame()

    def unload(self):
        self.config(image='')
        self.frames = []
        self.loc = 0
        self.delay = 0

        if hasattr(self, 'after_id') and self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def next_frame(self):
        if self.frames:
            self.location += 1
            self.location %= len(self.frames)

            frame = self.frames[self.location]
            self.config(image=frame, width=self.width, height=self.height, anchor='center')
            
            self.after_id = self.after(self.delay, self.next_frame)

class Application(tkinter.Tk):
    def __init__(
        self, 
        *args: Any, 
        paths: List[str], 
        duration: int = 1, 
        width: int = 720,
        height: int = 720,
        **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        self.height = height
        self.width = width

        if not paths:
            self.images: List[Tuple[Image.Image, str]] = []
        else:
            self.images: List[Tuple[Image.Image, str]] = self.load_images([pathlib.Path(path) for path in paths])

        self.duration = duration
        self.index = -1
        self.last_index = 0
        self.slideshow_id: Optional[str] = None
        self.current_image: Optional[Image.Image] = None
        self.is_fullscreen = False

        self.title('Image viewer')
        self.geometry(f'{self.width}x{self.height}')

        self.slide = ImageLabel(self)
        self.slide.pack()

        self.setup_menu()
        self.setup_keybinds()

    def setup_menu(self):
        root = tkinter.Menu(self)
        self.config(menu=root)

        root.add_command(label='Quit', command=self.destroy, accelerator='Ctrl+Q')
        root.add_command(label='Next', command=self.next, accelerator='Right')
        root.add_command(label='Previous', command=self.previous, accelerator='Left')
        root.add_command(label='Slideshow', command=self.slideshow, accelerator='Space')
        root.add_command(label='Shuffle', command=self.shuffle, accelerator='Ctrl+S')
        root.add_command(label='Random', command=self.random, accelerator='Ctrl+R')
        root.add_command(label='Back', command=self.back, accelerator='Ctrl+B')
        root.add_command(label='Goto', command=self.goto, accelerator='Ctrl+G')

    def setup_keybinds(self):
        self.bind('<Right>', self.next)
        self.bind('<Left>', self.previous)
        self.bind('<Escape>', self.destroy)
        self.bind('<space>', self.slideshow)
        self.bind('<Control-s>', self.shuffle)
        self.bind('<Control-r>', self.random)
        self.bind('<Control-b>', self.back)
        self.bind('<Control-g>', self.goto)
        self.bind('<Control-q>', self.destroy)
        self.bind('<F11>', self.fullscreen)

    def open_image(self, path: pathlib.Path) -> Tuple[Image.Image, str]:
        return self.resize(Image.open(path), path.name), path.name

    def load_images(self, paths: List[pathlib.Path]) -> List[Tuple[Image.Image, str]]:
        images: List[Tuple[Image.Image, str]] = []
        failed = 0

        for dir in paths:
            for file in dir.iterdir():
                try:
                    image = self.resize(Image.open(file), file.name)
                    images.append((image, file.name))
                except UnidentifiedImageError:
                    logger.error('Error while loading %r.', file.name, exc_info=True)
                    failed += 1
                else:
                    logger.info('Loaded %r with size %dx%d.', file.name, image.width, image.height)

        logger.info('Loaded %d/%d images.', len(images) - failed, len(images))
        return sorted(images, key=lambda image: _sort(image[1]))

    def resize(
        self, 
        image: Image.Image, 
        name: str, 
        *, 
        max_width: Optional[int] = None, 
        max_height: Optional[int] = None,
    ) -> Image.Image:
        max_width = max_width or self.width
        max_height = max_height or self.height

        width, height = image.width, image.height
        if width > height:
            ratio = max_height / width
            width = max_width
            height = math.ceil(height * ratio)
        else:
            ratio = max_width / height
            height = max_height
            width = math.ceil(width * ratio)

        if image.format == 'GIF':
            for frame in ImageSequence.Iterator(image):
                frame.resize((width, height))
            
            return image
 
        return image.resize((width, height))

    def set_image(self, image: Image.Image) -> None:
        self.current_image = image
        self.slide.load(image, self.width, self.height)

    def fullscreen(self, *args: Any) -> None:
        if self.is_fullscreen:
            self.attributes('-fullscreen', False)
            self.is_fullscreen = False
        else:
            self.attributes('-fullscreen', True)
            self.is_fullscreen = True

    def show(self, image: Image.Image, name: str):
        self.slide.unload()
        self.set_image(image)

        logger.info('Showing %r', name)
        self.title(f'{name} | ({self.index + 1}/{len(self.images)})')

    def next(self, *args: Any) -> None:
        self.last_index = self.index
        self.index += 1

        try:
            image, name = self.images[self.index]
        except IndexError:
            self.index = 0
            image, name = self.images[self.index]

        self.show(image, name)

    def previous(self, *args: Any) -> None:
        self.last_index = self.index
        self.index -= 1
        if self.index < 0:
            self.index = len(self.images) - 1

        image, name = self.images[self.index]
        self.show(image, name)

    def _run_slideshow(self):
        self.next()
        self.slideshow_id = self.after(self.duration * 1000, self._run_slideshow)

    def slideshow(self, *args: Any) -> None:
        if self.slideshow_id is None:
            self._run_slideshow()
        else:
            self.after_cancel(self.slideshow_id)
            self.slideshow_id = None

    def shuffle(self, *args: Any) -> None:
        random.shuffle(self.images)
        self.index = -1

        self.next()

    def random(self, *args: Any) -> None:
        self.last_index = self.index
        self.index = random.randint(0, len(self.images) - 1)

        image, name = self.images[self.index]
        self.show(image, name)

    def goto(self, *args: Any) -> None:
        index = simpledialog.askinteger('Goto', 'Enter the index of the image you want to go to.', parent=self, minvalue=1, maxvalue=len(self.images))
        if index is not None:
            self.last_index = self.index
            self.index = index - 1

            image, name = self.images[self.index]
            self.show(image, name)

    def back(self, *args: Any) -> None:
        if self.last_index < 0:
            self.last_index = 0

        self.index = self.last_index
        image, name = self.images[self.index]

        self.show(image, name)

    def destroy(self, *args: Any) -> None:
        if self.is_fullscreen:
            self.attributes('-fullscreen', False)
            self.is_fullscreen = False
        else:
            super().destroy()

    def run(self):
        self.mainloop()

def main():
    parser = argparse.ArgumentParser(description='An Image viewer.')

    parser.add_argument(
        'path', type=str, help='Path to the directory containing the images.'
    )

    parser.add_argument(
        '--width', 
        type=int, 
        help='Width of the window. Defaults to 720. Images are resized according to this argument.', 
        default=720
    )

    parser.add_argument(
        '--height', 
        type=int, 
        help='Height of the window. Defaults to 720. Images are resized according to this argument.', 
        default=720
    )

    parser.add_argument('--debug', action='store_true', help='Print debug messages.', default=False)

    args = parser.parse_args()

    if not args.debug:
        logger.setLevel(logging.ERROR)

    app = Application(width=args.width, height=args.height, paths=[args.path])

    app.run()
    return 0

if __name__ == '__main__':
    exit(main())