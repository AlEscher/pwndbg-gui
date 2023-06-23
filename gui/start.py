import logging

from gui.gui import run_gui

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)


def main():
    logger.info("Starting GUI")
    run_gui()


if __name__ == "__main__":
    main()
