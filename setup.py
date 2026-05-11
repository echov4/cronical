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
# name of the device
DEVICE_NAME = ""
DEVICE_FILE = ""

# Get the device name and check if it already exists as a folder in /crons
while True:
    DEVICE_NAME = str(input("Enter in the name of the device: \t"))
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

# if the job is not in the crontabs, then add the watcher script there
if watcher_added_status == False:
    job = cron.new(command=watcher_command)
    job.minute.every(5)
    job.set_comment("cron-cal-watcher")
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

# save the current cronjobs to the device file
with open(DEVICE_FILE, "w") as f:
    f.write(original_cronjobs.stdout)


# setup the .env file if it does not exist
if not os.path.isfile(PATH / ".env"):
    with open(".env", "w") as f:
        f.writelines(f"DEVICE_NAME={DEVICE_NAME}\n")
        f.writelines(f"DEVICE_PATH={DEVICE_FILE}\n")
        f.writelines("GITHUB_PAT=\n")
        f.writelines("OTHER=\n")
    print(".env file has been created and needs to be filled in")
else:
    print(".env file already exists")

