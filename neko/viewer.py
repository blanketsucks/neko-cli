from __future__ import annotations

from typing import Any, List, Optional, Tuple

from PIL import Image, ImageTk, UnidentifiedImageError, ImageSequence
from tkinter import simpledialog
from itertools import count
from enum import Enum
import argparse
import random
import tkinter
import pathlib
import math

class Colors(str, Enum):
    red = '\u001b[1;31m'
    green = '\u001b[1;32m'
    white = '\u001b[1;37m'
    reset = '\u001b[0m'

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
        self.slideshow: Optional[str] = None
        self.current_image: Optional[Image.Image] = None

        self.title('Image viewer')
        self.geometry(f'{self.width}x{self.height}')

        self.slide = ImageLabel(self)
        self.slide.pack()

        self.setup_menu()
        self.setup_keybinds()

    def _destroy(self, *args: Any) -> None:
        self.destroy()

    def setup_menu(self):
        root = tkinter.Menu(self)
        self.config(menu=root)

        root.add_command(label='Quit', command=self.destroy, accelerator='Ctrl+Q')
        root.add_command(label='Next', command=self.next, accelerator='Right')
        root.add_command(label='Previous', command=self.previous, accelerator='Left')
        root.add_command(label='Slideshow', command=self.start_slideshow, accelerator='Space')
        root.add_command(label='Shuffle', command=self.shuffle, accelerator='Ctrl+S')
        root.add_command(label='Random', command=self.random, accelerator='Ctrl+R')
        root.add_command(label='Goto', command=self.goto, accelerator='Ctrl+G')

    def setup_keybinds(self):
        self.bind('<Right>', self.next)
        self.bind('<Left>', self.previous)
        self.bind('<Escape>', self._destroy)
        self.bind('<space>', self.start_slideshow)
        self.bind('<Control-s>', self.shuffle)
        self.bind('<Control-r>', self.random)
        self.bind('<Control-g>', self.goto)
        self.bind('<Control-q>', self._destroy)

    def open_image(self, path: pathlib.Path) -> Tuple[Image.Image, str]:
        image = self.resize(Image.open(path), path.name)
        return image, path.name

    def load_images(self, paths: List[pathlib.Path]) -> List[Tuple[Image.Image, str]]:
        images: List[Tuple[Image.Image, str]] = []
        failed = 0

        for path in paths:
            for image in path.iterdir():
                if image.is_file():
                    try:
                        images.append(self.open_image(image))
                    except UnidentifiedImageError:
                        fmt = f'{Colors.white}- {image.name}{Colors.reset}: {Colors.red}Error while loading.{Colors.reset}'
                        failed += 1
                    else:
                        fmt = f'{Colors.white}- {image.name}{Colors.reset}: {Colors.green}Loaded.{Colors.reset}'
                    
                    print(fmt)

        length = len(images)
        print(f'\n{Colors.white}- Loaded {length-failed}/{length} images.{Colors.reset}')

        return images

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

        print(f'{Colors.white}- {name}{Colors.reset}: {Colors.green}Resized to {width}x{height}.{Colors.reset}')
        if image.format == 'GIF':
            for frame in ImageSequence.Iterator(image):
                frame.resize((width, height))
            
            return image
 
        return image.resize((width, height))

    def set_image(self, image: Image.Image) -> None:
        self.current_image = image
        self.slide.load(image, self.width, self.height)

    def show(self, image: Image.Image, name: str):
        self.slide.unload()
        self.set_image(image)

        self.title(name + f' | ({self.index + 1}/{len(self.images)})')

    def next(self, *args: Any) -> None:
        self.index += 1
        self.frames = 0

        try:
            image, name = self.images[self.index]
        except IndexError:
            self.index = 0
            image, name = self.images[self.index]

        self.show(image, name)

    def previous(self, *args: Any) -> None:
        self.index -= 1
        self.frames = 0

        if self.index < 0:
            self.index = len(self.images) - 1

        image, name = self.images[self.index]
        self.show(image, name)

    def _run_slideshow(self):
        self.next()
        self.slideshow = self.after(self.duration * 1000, self._run_slideshow)

    def start_slideshow(self, *args: Any) -> None:
        if self.slideshow is None:
            self._run_slideshow()
        else:
            self.after_cancel(self.slideshow)
            self.slideshow = None

    def shuffle(self, *args: Any) -> None:
        random.shuffle(self.images)
        self.index = -1

        self.next()

    def random(self, *args: Any) -> None:
        self.index = random.randint(0, len(self.images) - 1)
        image, name = self.images[self.index]

        self.show(image, name)

    def goto(self, *args: Any) -> None:
        index = simpledialog.askinteger('Goto', 'Enter the index of the image you want to go to.', parent=self, minvalue=1, maxvalue=len(self.images))
        if index is not None:
            self.index = index - 1

            image, name = self.images[self.index]
            self.show(image, name)

    def run(self):
        self.mainloop()

def main():
    parser = argparse.ArgumentParser(description='An Image viewer.')

    parser.add_argument('--path', type=str, help='Path to the directory containing the images.', default='./images')
    parser.add_argument('--width', type=int, help='Width of the window. Defaults to 720. Images are resized according to this argument.', default=720)
    parser.add_argument('--height', type=int, help='Height of the window. Defaults to 720. Images are resized according to this argument.', default=720)

    args = parser.parse_args()
    app = Application(width=args.width, height=args.height, paths=[args.path])

    app.run()
    return 0

if __name__ == '__main__':
    exit(main())