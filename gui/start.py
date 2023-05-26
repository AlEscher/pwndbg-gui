import logging

from gui import run_gui
from pty_util import create_pty_devices

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)


def main():
    logger.info("Creating PTY devices")
    ttys = create_pty_devices()
    logger.info("Starting GUI")
    run_gui(ttys=ttys)


if __name__ == "__main__":
    main()
