import subprocess
import os
from crontab import CronTab
from pathlib import Path
import shutil


# gets the crontabs of the current user only
cron = CronTab(user=True)

# global
PATH = Path(__file__).parent
WATCHER_FILE = "cron-watcher.py"
CRONS_DIRECTORY= "crons"

# checks to see if git is installed, and the .venv exists
def checkup_and_set_environment():
    # check if git is installed
    if shutil.which("git") is None:
        print("Error: git is not installed, will need to install before running the script")
        exit(1)
    else:
        print("Git is installed")

    # make a .venv folder
    if ".venv" not in os.listdir(PATH):
        print(".venv does not exist, run `uv sync`")
        exit(1)
    else:
        print(".venv is already created")

    # get the .venv runtime path
    python_venv_runtime = f"{PATH}/.venv/bin/python"

    # return the path to the python runtime for the cronjob runtime
    return python_venv_runtime


# check and create the crons folder
def create_cron_folder():
    if CRONS_DIRECTORY in os.listdir(PATH):
        print(f"{CRONS_DIRECTORY}/ directory already exists")
    else:
        os.mkdir(PATH/CRONS_DIRECTORY)
        print(f"Created the {CRONS_DIRECTORY}/ directory")


# Get the device name and check if it already exists as a file in /crons, if not then create it
# returns the device name in string, and device file path
def create_device_file():
    while True:
        device_input = str(input("Enter in the name of the device file (no spaces): \t"))

        # if device name is empty then throw error and try again
        if not device_input or " " in device_input:
            print("ERROR: Device file name cannot be empty or contain spaces")
            continue

        device_name = device_input.split()[0]
        device_file = PATH / CRONS_DIRECTORY / f"{device_name}.txt"

        # create the device file
        try:
            device_file.open("x").close()
            print(f"Device file {device_file} is created")
            break
        except FileExistsError:
            print("ERROR: Device file already exists")
            print(f"- Check if {device_file} already exists and added already")
            print(F"- Check if {device_file} is a name for another device")
            print("- If it is a new device, enter in a different name for this device ")
    return device_file, device_name

# add the watcher script to the original cronjob for every minute update
def add_watcher_to_crontab(python_runtime_path):
    watcher_command = f"{python_runtime_path} {PATH}/{WATCHER_FILE}"

    # check if the watcher script is already added into the cronjobs
    watcher_added_status = False
    for job in cron:
        if watcher_command in job.command:
            watcher_added_status = True
            break

    # if the watcher script command is not in the original cronjobs, then add the watcher script command
    if watcher_added_status == False:
        job = cron.new(command=watcher_command)
        job.minute.every(1)
        job.set_comment("cronical-watcher")
        cron.write()
        print("Added the watcher script command in the original cronjob, the command:\n" + watcher_command)
    else:
        print("Watcher file command is already in the original cronjob")

# append the newly created device file with all the contents of all the original cronjobs
def add_original_cronjobs_to_device_file(device_file):
    # get the original cronjobs from command
    original_cronjobs = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True
    )

    # save the original cronjobs to the device file if it has read correctly
    if original_cronjobs.returncode == 0:
        with open(device_file, "w") as f:
            f.write(original_cronjobs.stdout)
    else:
        print("Error reading cronjobs")

# setup the env file if it does not exist
def setup_env_file(device_file, device_name):
    if not os.path.isfile(PATH / ".env"):
        github_user = input("Enter in your github username (case sensitive)\t")
        github_repo_name = input("Enter in the repo of the github (case sensitive)\t")
        github_pat = input("Enter in your github PAT code\t")

        with open(PATH / ".env", "w") as f:
            f.writelines(f"DEVICE_NAME={device_name}\n")
            f.writelines(f"DEVICE_PATH={device_file}\n")
            f.writelines(f"GITHUB_PAT={github_pat}\n")
            f.writelines(f"GITHUB_USER={github_user}\n")
            f.writelines(f"GITHUB_REPO_NAME={github_repo_name}\n")

        print(".env file has been created and needs to be filled in")
    else:
        print(".env file already exists")

# sets the .gitignore file and adds the .env file in there
def setup_gitignore():
    # check if gitignore exists
    gitignore = PATH / ".gitignore"
    if not gitignore.exists():
        gitignore.open("w").close()
        print("Creating a .gitignore file")
    else:
        print("gitignore file already exists")

    # check if .env file is in the gitignore
    if ".env" not in gitignore.read_text():
        with open(gitignore, "a") as f:
            f.write("\n.env\n")
        print(".env added to .gitignore")
    else:
        print(".env already in .gitignore")


# MAIN
python_runtime_path = checkup_and_set_environment()
# create_cron_folder()
# device_file, device_name = create_device_file()
add_watcher_to_crontab(python_runtime_path)
# add_original_cronjobs_to_device_file(device_file)
# setup_env_file(device_file, device_name)
# setup_gitignore()
# print("SETUP COMPLETED")