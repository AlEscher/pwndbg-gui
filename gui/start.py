import logging

import sys
from os import path
directory, file = path.split(__file__)
directory = path.expanduser(directory)
directory = path.join(directory, "..")
directory = path.abspath(directory)
sys.path.append(directory)

from pwndbg_gui import run_gui

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s | [%(levelname)s] : %(message)s')
logger = logging.getLogger(__file__)


def main():
    logger.info("Starting GUI")
    run_gui()


if __name__ == "__main__":
    main()
