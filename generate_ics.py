# get all the the files in crons/ and their contents

# store as a dict
# remove all the comments and strip and trim the jobs

# get the time for each job and parse it to date time in ICS
# generate the ICS file
# save it to the public folder
# BONUS: test it with the cloudflare and subscribe to it

from pathlib import Path
import os
from crontab import CronTab

from ics import Calendar, Event
from datetime import datetime


PATH = Path(__file__).parent
CRONS_DIRECTORY = "crons"

# list of  dicts of all cronjobs
ALL_CRONS = []


# gets the crons of each file
def get_device_file_crons():
    # get all the files
    all_device_files= os.listdir(PATH/CRONS_DIRECTORY)

    # check if at least one file exists
    if len(all_device_files) == 0:
        print("Error: no device files, need to set it up")
        exit(1)

    # get all the contents of the files and parse them
    for file in all_device_files:
        file_contents = ((PATH/CRONS_DIRECTORY/file).read_text())
        parse_crons(file, file_contents)


# parse the file contents of the file and save it to the ALL_CRONS
def parse_crons(file, file_contents):
    cron = CronTab(tab=file_contents)
    for job in cron:
        ALL_CRONS.append(
            {
                "device":Path(file).stem,
                "raw-cron":job,
                "cron-time":str(job.slices),
                "command": job.command,
                "comments": job.comment,
            }
        )

def generate_date_time_for_cronjob():
    pass




def generate_ics_file():
    pass



def save_ics_file():
    pass










get_device_file_crons()



# testing
for cron in ALL_CRONS:
    print(f"Device: {cron['device']}")
    print(f"Raw: {cron['raw-cron']}")
    print(f"Time: {cron['cron-time']}")
    print(f"Command: {cron['command']}")
    print(f"Comments: {cron['comments']}")
    print("\n\n\n")