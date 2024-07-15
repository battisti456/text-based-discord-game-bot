from typing import override
import logging

LOGGING_LEVEL = 'INFO'

class Color_Filter(logging.Filter):
    start_grey = "\x1b[38;20m"
    start_blue:str = "\u001b[34m"
    start_green:str=  "\u001b[32m"
    start_yellow = "\x1b[33;20m"
    start_red = "\x1b[31;20m"
    start_bold_red = "\x1b[31;1m"
    color = {
        logging.DEBUG : start_green,
        logging.INFO : start_blue,
        logging.WARNING : start_yellow,
        logging.ERROR : start_red,
        logging.CRITICAL : start_bold_red
    }
    color_end = "\x1b[0m"
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        try:
            record.start_color = Color_Filter.color[record.levelno]
        except IndexError:
            record.start_color = Color_Filter.start_grey
        record.end_color = Color_Filter.color_end
        return record

fmt = logging.Formatter('%(start_color)s%(asctime)s::%(levelname)s%(end_color)s::%(name)s::%(message)s')
flt = Color_Filter()
h1 = logging.StreamHandler()
h1.setLevel(LOGGING_LEVEL)
h1.setFormatter(fmt)

def get_logger(name:str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addFilter(flt)
    logger.addHandler(h1)
    logger.setLevel(LOGGING_LEVEL)
    return logger