from typing import Tuple, List

import logging

from neko.utils import Colors

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
    logger = logging.getLogger('neko')
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter())

    logger.addHandler(handler)
    return logger