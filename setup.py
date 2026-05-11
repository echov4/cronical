import subprocess
import os
from crontab import CronTab
from pathlib import Path


# gets the crontabs of the current user only
cron = CronTab(user=True)

# path of directories
PATH = Path(__file__).parent
WATCHER_FILE = "cron-watcher.py"
CRONS_DIRECTORY= "crons"


# check and create the crons/ folder
if "crons" in os.listdir(PATH):
    print("crons/ directory exists")
else:
    os.mkdir(PATH/"crons")
    print("Created crons/ directory")
# Get the device name and check if it already exists as a file in /crons
while True:
    device_input = str(input("Enter in the name of the device: \t"))

    # if device name is empty then throw error
    if not device_input:
        print("ERROR: Device name cannot be empty")
        continue

    DEVICE_NAME = device_input.split()[0]
    DEVICE_FILE = PATH / CRONS_DIRECTORY / f"{DEVICE_NAME}.txt"

    try:
        DEVICE_FILE.open("x").close()
        print(f"Device cron file {PATH}/{CRONS_DIRECTORY}/{DEVICE_NAME} is created")
        break
    except FileExistsError:
        print("ERROR: Device cron file already exists")
        print(f"- Check if {PATH}/{DEVICE_NAME} already exists and added already")
        print(F"- Check if {PATH}/{DEVICE_NAME} is a name for another device")
        print("- If it is a new device, enter in a different name for this device ")


# add the watcher script to the cronjob for every 5 minutes update
watcher_command = f"python {PATH}/{WATCHER_FILE}"

# check if the watcher is already added into the cronjobs
watcher_added_status = False
for job in cron:
    if watcher_command in job.command:
        watcher_added_status = True
        break

# if the job is not in the crontabs, then add the watcher script there
if watcher_added_status == False:
    job = cron.new(command=watcher_command)
    job.minute.every(5)
    job.set_comment("cronical-watcher")
    cron.write()
    print("Added the watcher script as a cron job with the command\n\t" + watcher_command)
else:
    print("Cronjob is already added in the cronjobs file")


# append the device file with all the contents of the cronjobs
# get the original cronjobs from command
original_cronjobs = subprocess.run(
    ["crontab", "-l"],
    capture_output=True,
    text=True
)

# save the current cronjobs to the device file if it has read correctly
if original_cronjobs.returncode == 0:
    with open(DEVICE_FILE, "w") as f:
        f.write(original_cronjobs.stdout)
else:
    print("Error reading cronjobs")

# setup the .env file if it does not exist
if not os.path.isfile(PATH / ".env"):
    with open(PATH / ".env", "w") as f:
        f.writelines(f"DEVICE_NAME={DEVICE_NAME}\n")
        f.writelines(f"DEVICE_PATH={DEVICE_FILE}\n")
        f.writelines("GITHUB_PAT=\n")
        f.writelines("OTHER=\n")
    print(".env file has been created and needs to be filled in")
else:
    print(".env file already exists")


# check the .gitignore file and add the .env in there
gitignore = PATH / ".gitignore"
if not gitignore.exists():
    gitignore.open("w").close()
    print("Creating a .gitignore file")
else:
    print("gitignore file already exists")

if ".env" not in gitignore.read_text():
    with open(gitignore, "a") as f:
        f.write("\n.env\n")
    print(".env added to .gitignore")
else:
    print(".env already in .gitignore")