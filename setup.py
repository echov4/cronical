import subprocess
import os
from crontab import CronTab
from pathlib import Path
import shutil

from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# gets the cron tabs of the current user only
cron = CronTab(user=True)

# global
PATH = Path(__file__).parent
WATCHER_FILE = "cron-watcher.py"
CRONS_DIRECTORY= "crons"

# need to make the logs directory if it does not exist for the logging to work
(PATH / "logs").mkdir(exist_ok=True)

# setup logging with 1MB limit and keep 3 backups
rotating_handler = RotatingFileHandler(
    PATH / "logs" / "cronical.log",
    maxBytes=1_000_000,
    backupCount=3
)

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        rotating_handler,
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("setup")


# checks to see if git is installed, and the .venv exists
def checkup_and_set_environment():
    # check if git is installed
    if shutil.which("git") is None:
        logger.error("ERROR: git is not installed, will need to install before running the script")
        exit(1)
    else:
        logger.info("Git is installed")

    # make a .venv folder
    if ".venv" not in os.listdir(PATH):
        logger.error("ERROR: .venv does not exist, run `uv sync`")
        exit(1)
    else:
        logger.info(".venv is already created")

    # get the .venv runtime path
    python_venv_runtime_path = f"{PATH}/.venv/bin/python"

    # return the path to the python runtime for the cronjob runtime
    return python_venv_runtime_path


# check and create the crons folder
def create_cron_folder():
    if CRONS_DIRECTORY in os.listdir(PATH):
        logger.info(f"{CRONS_DIRECTORY}/ directory already exists")
    else:
        os.mkdir(PATH/CRONS_DIRECTORY)
        logger.info(f"Created the {CRONS_DIRECTORY}/ directory")


# check if public folder if not there, create it
def create_public_folder():
    if "public" in os.listdir(PATH):
        logger.info("public/ directory already exists")
    else:
        os.mkdir(PATH / "public")
        logger.info("Created public/ directory")

# Get the device name and check if it already exists as a file in /crons, if not then create it
# returns the device name in string, and device file path
def create_device_file():
    while True:
        device_input = str(input("Enter in the name of the device file (no spaces): \t"))

        # if device name is empty then throw error and try again
        if not device_input or " " in device_input:
            logger.error("ERROR: Device file name cannot be empty or contain spaces")
            continue

        device_name = device_input.split()[0]
        device_file = PATH / CRONS_DIRECTORY / f"{device_name}.txt"

        # create the device file
        try:
            device_file.open("x").close()
            logger.info(f"Device file {device_file} is created")
            break
        except FileExistsError:
            logger.error("ERROR: Device file already exists")
            logger.error(f"- Check if {device_file} already exists and added already")
            logger.error(f"- Check if {device_file} is a name for another device")
            logger.error("- If it is a new device, enter in a different name for this device ")
    return device_file, device_name


# add the watcher script to the original cron tab for every minute update
def add_watcher_to_crontab(python_venv_runtime_path):
    watcher_command = f"{python_venv_runtime_path} {PATH}/{WATCHER_FILE}"

    # check if the watcher script is already added into the cron tab
    watcher_added_status = False
    for job in cron:
        if watcher_command in job.command:
            watcher_added_status = True
            break

    # if the watcher script command is not in the original cron tab, then add the watcher script command
    if watcher_added_status == False:
        job = cron.new(command=watcher_command)
        job.minute.every(1)
        job.set_comment("cronical-watcher")
        cron.write()
        logger.info("cron-watcher.py script command added in the original cron tab, the command:\n" + watcher_command)
    else:
        logger.info("cron-watcher.py file command is already in the original cron tab")


# append the newly created device file with all the contents of all the original cron tabs
def add_original_cronjobs_to_device_file(device_file):
    # get the original cron tabs from command
    original_cronjobs = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True
    )

    # save the original cron tabs to the device file if it has read correctly
    if original_cronjobs.returncode == 0:
        with open(device_file, "w") as f:
            f.write(original_cronjobs.stdout)
        logger.info(f"Original cron jobs have been added to the device file {device_file}")
    else:
        logger.error(f"ERROR: cannot read original cron jobs to add to the device file {device_file}")


# setup the env file if it does not exist
def setup_env_file(device_file, device_name):
    github_user = input("Enter in your github username (case sensitive)\t")
    github_repo_name = input("Enter in the repo of the github (case sensitive)\t")
    github_pat = input("Enter in your github PAT code\t")

    with open(PATH / ".env", "w") as f:
        f.writelines(f"DEVICE_NAME={device_name}\n")
        f.writelines(f"DEVICE_PATH={device_file}\n")
        f.writelines(f"GITHUB_PAT={github_pat}\n")
        f.writelines(f"GITHUB_USER={github_user}\n")
        f.writelines(f"GITHUB_REPO_NAME={github_repo_name}\n")
    logger.info("if .env file already existed, it has been overwritten with the new values")
    logger.info(f".env file has been created at {PATH / '.env'}")

# sets the .gitignore file and adds the .env file in there
def setup_gitignore():
    # check if gitignore exists
    gitignore = PATH / ".gitignore"
    if not gitignore.exists():
        gitignore.open("w").close()
        logger.info(f"Creating a .gitignore file at {gitignore}")
    else:
        logger.info(f".gitignore file already exists at {gitignore}")

    # check if .env file is in the gitignore
    if ".env" not in gitignore.read_text():
        with open(gitignore, "a") as f:
            f.write(".env\n")
        logger.info(f".env added to .gitignore at {gitignore}")
    else:
        logger.info(f".env already in .gitignore at {gitignore}")

    # check if .venv/ folder is in gitignore
    if ".venv/" not in gitignore.read_text():
        with open(gitignore, "a") as f:
            f.write(".venv/\n")
        logger.info(f".venv/ added in .gitignore at {gitignore}")
    else:
        logger.info(f".venv/ already in .gitignore at {gitignore}")



# MAIN
python_venv_runtime_path = checkup_and_set_environment()
create_cron_folder()
create_public_folder()
device_file, device_name = create_device_file()
add_watcher_to_crontab(python_venv_runtime_path)
add_original_cronjobs_to_device_file(device_file)
setup_env_file(device_file, device_name)
setup_gitignore()
logger.info("Setup completed")