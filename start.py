import argparse
import getpass
import logging
import subprocess
import sys
import venv
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s | [%(levelname)s] : %(message)s')
logger = logging.getLogger(__file__)


def create_virtual_environment(env_dir: Path):
    """Create a new Python virtual environment."""
    if not env_dir.exists():
        logger.info("Creating virtual environment at %s", str(env_dir))
        venv.create(env_dir, with_pip=True)


def install_dependencies(env_dir: Path, requirements_file: Path):
    """Install dependencies in the virtual environment using pip."""
    pip_path = f"{env_dir}/Scripts/pip" if sys.platform == "win32" else f"{env_dir}/bin/pip"
    logger.info("Installing requirements from %s for %s", str(requirements_file), str(env_dir))
    subprocess.run([pip_path, "install", "-r", requirements_file], check=True)


def run_script_in_environment(env_dir: Path, script_path: Path, args: argparse.Namespace):
    """Run the Python script within the virtual environment."""
    python_path = f"{env_dir}/Scripts/python" if sys.platform == "win32" else f"{env_dir}/bin/python"
    logger.info("Starting GUI using venv %s", str(env_dir))
    cmd = [python_path, script_path, args.log]
    if args.sudo:
        cmd = ["sudo", "-S"] + cmd
        password = getpass.getpass("Enter your sudo password: ")
        password = password.strip()
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        process.communicate(password.encode())
    else:
        subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sudo", action="store_true", help="Run the script with sudo. This is required if you want "
                                                            "GDB to attach to a running process")
    parser.add_argument("-log", help="Set the log level of the GUI", default="INFO")
    args = parser.parse_args()
    root_dir = Path(__file__).parent.resolve()
    env_dir = root_dir / "pwndbg-gui-venv"
    requirements_file = root_dir / "requirements.txt"
    script_path = root_dir / "gui" / "pwndbg_gui.py"

    create_virtual_environment(env_dir)
    install_dependencies(env_dir, requirements_file)
    run_script_in_environment(env_dir, script_path, args)


if __name__ == "__main__":
    main()
