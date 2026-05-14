from pathlib import Path
import os
from crontab import CronTab
from datetime import datetime



PATH = Path(__file__).parent
CRONS_DIRECTORY = "crons"
# list of  dicts of all cronjobs
ALL_CRONS = []

# threshold for how many days to create jobs for
HORIZON_DAYS = 90
# minimum job length in minutes for it to be an all day event
ALLDAY_THRESHOLD_MINUTES = 10


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
                "human-time": job.description(),
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











# MAIN
get_device_file_crons()


# for job in ALL_CRONS:
#     print(job["human-time"])