from pathlib import Path
import os
from crontab import CronTab
from datetime import datetime, timedelta
from croniter import croniter, croniter_range
from icalendar import Calendar, Event

import logging
from logging.handlers import RotatingFileHandler

PATH = Path(__file__).parent
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

logger = logging.getLogger("generate-ics")

CRONS_DIRECTORY = "crons"
# list of  dicts of all cronjobs
ALL_CRONS = []

# threshold for how many days to create jobs for on the calendar
HORIZON_DAYS = 365


# gets the crons of each file in crons/
def get_device_file_crons():
    # get all the files
    all_device_files= os.listdir(PATH/CRONS_DIRECTORY)

    # check if at least one file exists
    if len(all_device_files) == 0:
        logger.error("ERROR: no device files, need to set it up")
        exit(1)

    # get all the contents of the files and parse them and save them to ALL_CRONS
    for file in all_device_files:
        file_contents = ((PATH/CRONS_DIRECTORY/file).read_text())
        parse_crons(file, file_contents)
    logger.info(f"Parsed {len(ALL_CRONS)} cron jobs from {len(all_device_files)} device files")


# parse the file contents of the file and save it to the ALL_CRONS
def parse_crons(file, file_contents):
    cron = CronTab(tab=file_contents)
    for job in cron:
        # checks to see if it is a valid job and is not commented out
        if job.is_enabled():
            ALL_CRONS.append(
                {
                    "device":Path(file).stem,
                    "raw-cron":job,
                    "cron-time":str(job.slices),
                    "human-time": job.description(),
                    "command": job.command,
                    "command-script": get_command_name(job.command),
                    "comments": job.comment,
                    # next runs will be generated using generate_next_runs() function
                    "next-runs": [],
                    "is-allday": False,
                }
            )


# generates the next runs for each cron job and saves it to ALL_CRONS
def generate_next_runs():
    # get the current date time and the horizon date time
    now = datetime.now()
    horizon = now + timedelta(days=HORIZON_DAYS)

    for job in ALL_CRONS:
        cron_time = job["cron-time"]

        # get the occurrences of the cron job between now and the horizon using croniter_range
        try:
            occurrences = list(croniter_range(now, horizon, cron_time))
            logger.info(f"Generated {len(occurrences)} occurrences for cron job '{job['command-script']}' with schedule '{job['human-time']}'")
        except Exception as e:
            logger.warning(f"Skipping invalid expression {cron_time}: {e}")
            continue

        # all the dates the job runs on (no times)
        dates = [dt.date() for dt in occurrences]

        # if any date for this job appears more than once, it SHOULD mean the job runs multiple times that day
        # will add only the dates it runs and mark it as an all day event
        if len(dates) != len(set(dates)):
            logger.info(f"Cron job '{job['command-script']}' runs multiple times a day, marking it as an all day event")
            job["next-runs"] = sorted(set(dates))
            job["is-allday"] = True
        # if it does not run multiple times  a day, it is added as a single event from the occurrences list
        else:
            logger.info(f"Cron job '{job['command-script']}' runs once a day, marking it as a single event")
            job["next-runs"] = occurrences


# using ALL_CRONS, generate the ics file
def generate_ics_file():
    # create a icalendar object and preamble
    cal = Calendar()
    cal.add("prodid", "-//Cronical//cronical//EN")
    cal.add("version", "2.0")
    cal.add("X-WR-CALNAME", "Cronical")

    # read the contents of all crons
    for job in ALL_CRONS:
        # if the job is marked as all day -> make it an all day events
        if job["is-allday"]:
            for day in job["next-runs"]:
                event = Event()
                event.add("summary", f"[{job['device']}] - {job['command-script']} (runs {job['human-time']})")
                event.add("description", f"Schedule: {job['human-time']}\nFull Command: {job['command']}\nComments: {job['comments']}")
                event.add("dtstart", day)
                event.add("dtend", day + timedelta(days=1))
                cal.add_component(event)

        # if job is not marked as all all day -> make individual events
        else:
            for dt in job["next-runs"]:
                event = Event()
                event.add("summary", f"[{job['device']}] - {job['command-script']}")
                event.add("description", f"Schedule: {job['human-time']}\nFull Command: {job['command']}\nComments: {job['comments']}")
                event.add("dtstart", dt)
                event.add("dtend", dt + timedelta(minutes=1))
                cal.add_component(event)
    logger.info(f"Generated calendar with {len(cal.subcomponents)} events from {len(ALL_CRONS)} cron jobs for {HORIZON_DAYS} days")
    return cal


# save the ics file from ALL_CRONS
def save_ics_file(cal):
    output_path = PATH / "public" / "calendar.ics"
    with open(output_path, "wb") as f:
        f.write(cal.to_ical())
    logger.info(f"Calendar saved to {output_path}")


# remove the path from the command for clarity
def get_command_name(command):
    command_trimmed = Path(command).name
    return command_trimmed


# # MAIN
get_device_file_crons()
generate_next_runs()
cal = generate_ics_file()
save_ics_file(cal)
