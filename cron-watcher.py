# Monitor the changes in the cronjob files and current file
# If there is a change
    # Pulls the repo
    # Update the local cronjobs
    # Push it up to GitHub

import os
import subprocess
from crontab import CronTab
from dotenv import load_dotenv
from pathlib import Path

PATH = Path(__file__).parent
# load the .env file
load_dotenv()
# get the device name and file path
DEVICE_NAME = os.getenv("DEVICE_NAME")
DEVICE_FILE_PATH = os.getenv("DEVICE_PATH")
GITHUB_PAT = os.getenv("GITHUB_PAT")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")
GITHUB_USER = os.getenv("GITHUB_USER")
REMOTE_URL = f"https://{GITHUB_PAT}@github.com/{GITHUB_USER}/{GITHUB_REPO_NAME}.git"

# gets the crontabs of the current user only
cron = CronTab(user=True)


def git_pull():
    result = subprocess.run(
        ["git", "-C", str(PATH), "pull", "--rebase", REMOTE_URL],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error pulling: {result.stderr}")
        exit(1)
    print("Repo pulled")


def git_add():
    result = subprocess.run(
        ["git",  "-C", str(PATH), "add", "."],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error adding: {result.stderr}")
        exit(1)
    print("Repo added")


def git_commit():
    result = subprocess.run(
        ["git",  "-C", str(PATH), "commit", "-m", f"auto: update crons [{DEVICE_NAME}]"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error committing: {result.stderr}")
        exit(1)
    print("Repo committed")

def git_push():
    result = subprocess.run(
        ["git",  "-C", str(PATH), "push"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error pushing: {result.stderr}")
        exit(1)
    print("Repo pushed")






def get_original_cronjobs():
    original_cronjobs = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True
    )

    if original_cronjobs.returncode == 0:
        return original_cronjobs
    else:
        exit(0)


# monitors the string output of the cronjobs compared to the device file
# returns True if there is changes, returns False if no changes
def monitor_cron_changes(original_cronjobs):
    device_cronjobs = Path(DEVICE_FILE_PATH).read_text()

    if device_cronjobs != original_cronjobs.stdout:
        return True
    else:
        return False


# adds the contents of the original cronjobs to the device file
def update_device_file(original_cronjobs):
    with open(DEVICE_FILE_PATH, "w") as f:
        f.write(original_cronjobs.stdout)



# MAIN
# if there are changes in the cronjob then execute the changes
original_cronjobs = get_original_cronjobs()
if monitor_cron_changes(original_cronjobs):
    print("different")
    update_device_file(original_cronjobs)
    git_add()
    git_commit()
    git_pull()
    # git_push()
else:
    print("same")
    pass