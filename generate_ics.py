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


PATH = Path(__file__).parent
CRONS_DIRECTORY = "crons/"

# list of  dicts
ALL_CRONS_FILES = []

def get_device_file_crons():
    # get all the files
    all_device_files= os.listdir(PATH/CRONS_DIRECTORY)

    # check if atleast one file exists
    if len(all_device_files) == 0:
        print("Error: no device files, need to set it up")
        exit(1)

    # get all the contents of the files
    for file in all_device_files:
        parse_crons(file)


        # print((PATH/CRONS_DIRECTORY/file).read_text())

    for a in ALL_CRONS_FILES:
        print(a)








def parse_crons(file):
    print(file)
    # contents = (PATH/CRONS_DIRECTORY/file).read_text()
    # cron = CronTab(tab="""
    # # backup job
    # */5 * * * * /usr/bin/python backup.py # run backup
    # """)

    # for job in cron:
    #     print(job.slices)      # cron timing
    #     print(job.command)     # command
    #     print(job.comment)     # comment



def generate_ics_file():
    pass




# get_device_file_crons()