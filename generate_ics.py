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
HORIZON_DAYS = 180
# minimum job length in minutes for it to be an all day event
ALLDAY_THRESHOLD_MINUTES = 30

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

# generate all th events of the job
def generate_next_runs():
    # get the current date, time and the horizon day date time
    now = datetime.now()
    horizon = now + timedelta(days=HORIZON_DAYS)

    for job in ALL_CRONS:
        cron_time = (job["cron-time"])

        # gets the iterator of jobs starting from now
        cron_iteration = croniter(cron_time, now)

        # get the first and second jobs in datetime and calculate the difference in minutes
        first_job = cron_iteration.get_next(datetime)
        second_job = cron_iteration.get_next(datetime)
        job_interval = (second_job - first_job).total_seconds() / 60

        # if the interval of the job is smaller than threshold - add an all day event in the next-runs in ALL_CRONS,
        if job_interval <= ALLDAY_THRESHOLD_MINUTES:
            # get all the dates from now, till the horizon
            job["next-runs"] = [now.date() + timedelta(days=i) for i in range(HORIZON_DAYS)]
            job["is-allday"] = True

        # # if not under the threshold, create a range of events for the job and add to the ALL_CRONS
        else:
            job["next-runs"] = list(croniter_range(now, horizon, job["cron-time"]))


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


# remove the path from the command
def get_command_name(command):
    commandtrimmed = Path(command).name
    return commandtrimmed


# # MAIN
get_device_file_crons()
generate_next_runs()
cal = generate_ics_file()
save_ics_file(cal)

# for job in ALL_CRONS:
#     print(
#         # "device", job["device"],
#         # "raw-cron", job["raw-cron"],
#         # "cron-time", job["cron-time"],
#         # "human time",job["human-time"],
#         # "command",(job["command"]),
#         # "command script",(job["command-script"]),
#         # "comments",job["comments"],
#         # "next runs",job["next-runs"],
#     )