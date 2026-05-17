import os
import subprocess
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

logger = logging.getLogger("cron-watcher")


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
        ["git",  "-C", str(PATH), "commit", "-m", f"[{DEVICE_NAME}]: update crons for device"],
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
        ["git", "-C", str(PATH), "push", REMOTE_URL, "main"],
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
        return original_cronjobs
    else:
        logger.error("Error: could not read original cron jobs")
        exit(1)


# monitors the string output of the cronjobs compared to the device file
# returns True if there is changes, returns False if no changes
def monitor_cron_changes(original_cronjobs):
    device_cronjobs = Path(DEVICE_FILE_PATH).read_text()

    if device_cronjobs != original_cronjobs.stdout:
        logger.info(f"Cron jobs have changed, syncing... with {DEVICE_FILE_PATH}")
        return True
    else:
        print(f"Cron jobs have not changed, no need to sync with {DEVICE_FILE_PATH}")
        return False


# adds the contents of the original cronjobs to the device file
def update_device_file(original_cronjobs):
    logger.info(f"Updating device file {DEVICE_FILE_PATH} with the latest cron jobs")
    with open(DEVICE_FILE_PATH, "w") as f:
        f.write(original_cronjobs.stdout)

# runs the generate_ics.py script locally to generate the ics files before pushing up to github instead of using github actions
def run_generate_ics_local():
    result = subprocess.run(
        [f"{PATH}/.venv/bin/python", str(PATH / "generate-ics.py")],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        logger.error(f"ERROR running generate_ics: {result.stderr}")
        logger.error(f"Output: {result.stdout}")
        exit(1)
    logger.info("generate_ics ran successfully")

# MAIN
# if there are changes in the cronjob then execute the changes
check_env_variables()
original_cronjobs = get_original_cronjobs()
if monitor_cron_changes(original_cronjobs):
    git_pull()
    update_device_file(original_cronjobs)
    # # run generate ics locally before adding, committing and pushing up instead of using github actions
    # run_generate_ics_local()
    git_add()
    git_commit()
    git_push()