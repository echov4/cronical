from pathlib import Path
import os
from crontab import CronTab
from datetime import datetime, timedelta
from croniter import croniter, croniter_range
from icalendar import Calendar, Event

PATH = Path(__file__).parent
CRONS_DIRECTORY = "crons"
# list of  dicts of all cronjobs
ALL_CRONS = []

# threshold for how many days to create jobs for
HORIZON_DAYS = 365
# minimum job length in minutes for it to be an all day event
ALLDAY_THRESHOLD_MINUTES = 1440 # 24 hours in minutes


# gets the crons of each file
def get_device_file_crons():
    # get all the files
    all_device_files= os.listdir(PATH/CRONS_DIRECTORY)

    # check if at least one file exists
    if len(all_device_files) == 0:
        print("Error: no device files, need to set it up")
        exit(1)

    # get all the contents of the files and parse them and save them to ALL_CRONS
    for file in all_device_files:
        file_contents = ((PATH/CRONS_DIRECTORY/file).read_text())
        parse_crons(file, file_contents)


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


def generate_next_runs():
    now = datetime.now()
    horizon = now + timedelta(days=HORIZON_DAYS)

    for job in ALL_CRONS:
        cron_time = job["cron-time"]

        try:
            occurrences = list(croniter_range(now, horizon, cron_time))
        except Exception as e:
            print(f"Skipping invalid expression {cron_time}: {e}")
            continue

        dates = [dt.date() for dt in occurrences]

        # if any date appears more than once, job runs multiple times that day
        if len(dates) != len(set(dates)):
            job["next-runs"] = sorted(set(dates))
            job["is-allday"] = True
        else:
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
        # if all day -> make it an all day events
        if job["is-allday"]:
            for day in job["next-runs"]:
                event = Event()
                event.add("summary", f"{job['device']} - {job['command-script']} (runs {job['human-time']})")
                event.add("description", f"Schedule: {job['human-time']}\nCommand: {job['command']}\nComments: {job['comments']}")
                event.add("dtstart", day)
                event.add("dtend", day + timedelta(days=1))
                cal.add_component(event)

        # if not all day -> make individual events
        else:
            for dt in job["next-runs"]:
                event = Event()
                event.add("summary", f"{job['device']} -  {job['command-script']}")
                event.add("description", f"Schedule: {job['human-time']}\nCommand: {job['command']}\nComments: {job['comments']}")
                event.add("dtstart", dt)
                event.add("dtend", dt + timedelta(minutes=1))
                cal.add_component(event)
    return cal


# save the ics file from ALL_CRONS
def save_ics_file(cal):
    output_path = PATH / "public" / "calendar.ics"

    with open(output_path, "wb") as f:
        f.write(cal.to_ical())
    print(f"Calendar saved to {output_path}")


# remove the path from the command for clarity
def get_command_name(command):
    command_trimmed = Path(command).name
    return command_trimmed


# # MAIN
get_device_file_crons()
generate_next_runs()
cal = generate_ics_file()
save_ics_file(cal)
