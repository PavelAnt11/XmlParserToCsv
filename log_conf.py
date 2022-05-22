import logging
import sys
from logging import FileHandler
FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
LOG_FILE = "xml_parser.log"


def get_file_handler(path):
    file_handler = FileHandler(path / LOG_FILE, mode='w')
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_logger(logger_name, path):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(path))
    logger.propagate = False
    return logger
