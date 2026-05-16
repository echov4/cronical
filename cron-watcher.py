import os
import subprocess
from crontab import CronTab
from dotenv import load_dotenv
from pathlib import Path

from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

PATH = Path(__file__).parent
# load the .env file
load_dotenv(PATH / ".env")
# get the device name and file path
DEVICE_NAME = os.getenv("DEVICE_NAME")
DEVICE_FILE_PATH = os.getenv("DEVICE_PATH")
GITHUB_PAT = os.getenv("GITHUB_PAT")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
GITHUB_USER = os.getenv("GITHUB_USER")
REMOTE_URL = f"https://{GITHUB_PAT}@github.com/{GITHUB_USER}/{GITHUB_REPO_NAME}.git"


# setup logging with 1MB limit and keep 3 backups
RotatingFileHandler(
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
        logging.FileHandler(PATH / "logs" / "cronical.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("cron-watcher")

# gets the crontabs of the current user only
cron = CronTab(user=True)


def check_env_variables():
    if not all([DEVICE_NAME, DEVICE_FILE_PATH, GITHUB_PAT, GITHUB_REPO_NAME, GITHUB_USER]):
        logger.error("ERROR: missing required .env variables, run setup.py first or fill it in")
        exit(1)


def git_pull():
    result = subprocess.run(
        ["git", "-C", str(PATH), "pull", "--rebase", REMOTE_URL, "main"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"ERROR pulling: {result.stderr}")
        logger.error(f"Output: {result.stdout}")
        exit(1)
    logger.info("Repo pulled")


def git_add():
    result = subprocess.run(
        ["git",  "-C", str(PATH), "add", "."],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"ERROR adding: {result.stderr}")
        logger.error(f"Output: {result.stdout}")
        exit(1)
    logger.info("Repo added")


def git_commit():
    result = subprocess.run(
        ["git",  "-C", str(PATH), "commit", "-m", f"auto: update crons for device [{DEVICE_NAME}]"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"ERROR committing: {result.stderr}")
        logger.error(f"Output: {result.stdout}")
        exit(1)
    logger.info(f"Repo committed")


def git_push():
    result = subprocess.run(
        ["git", "-C", str(PATH), "push", "origin", "main"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"ERROR pushing: {result.stderr}")
        logger.error(f"Output: {result.stdout}")
        exit(1)
    logger.info("Repo pushed")

# reads all the original crontabs
def get_original_cronjobs():
    original_cronjobs = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True
    )

    if original_cronjobs.returncode == 0:
        logger.info("Successfully read original cron jobs")
        return original_cronjobs
    else:
        logger.error("Error: could not read original cron jobs")
        exit(1)

# monitors the string output of the cronjobs compared to the device file
# returns True if there is changes, returns False if no changes
def monitor_cron_changes(original_cronjobs):
    device_cronjobs = Path(DEVICE_FILE_PATH).read_text()

    if device_cronjobs != original_cronjobs.stdout:
        logger.info("Cron jobs have changed, syncing...")
        return True
    else:
        print("Cron jobs have not changed, no need to sync")
        return False


# adds the contents of the original cronjobs to the device file
def update_device_file(original_cronjobs):
    with open(DEVICE_FILE_PATH, "w") as f:
        f.write(original_cronjobs.stdout)


# MAIN
# if there are changes in the cronjob then execute the changes
check_env_variables()
original_cronjobs = get_original_cronjobs()
if monitor_cron_changes(original_cronjobs):
    update_device_file(original_cronjobs)
    git_add()
    git_commit()
    git_pull()
    git_push()
else:
    print("No changes in cron jobs")
