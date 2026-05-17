# cronical
Turn your cron jobs into a subscribable calendar

> [!WARNING]
> Currently in Testing
>
> This has not been fully tested and changes may be required

## What is cronical?

`cronical` monitors the cron jobs on your device(s) and converts them into an `.ics` calendar file that can be hosted and subscribed to in any calendar app (Google Calendar, Apple Calendar, Outlook, etc.). Any changes to your cron jobs are automatically synced and reflected in your calendar.

---

## Overview

```
crontab changes on your device
        ↓
cron-watcher.py detects the change (runs every minute by default)
        ↓
commits and pushes to your GitHub repo
        ↓
GitHub Actions generates a merged calendar.ics from all devices
        ↓
calendar.ics is served publicly via your chosen hosting
        ↓
subscribe in Google Calendar, Apple Calendar, Outlook, etc.
```

### Key Features

- Supports multiple devices, all merged into one calendar
- Jobs that run multiple times a day appear as all-day events
- Jobs that run once a day or less appear as individual timed events
- Automatically syncs crontab changes
- Entirely free stack (GitHub, GitHub Actions, Cloudflare Pages or raw GitHub URL)
- Anyone can fork this repo to their own account and have it working for their own devices

---

## Directory Structure

```bash
.
├── crons/                          # crontab files, one per device
│   └── device.txt
├── logs/
│   ├── cronical.log                # local log, never committed (gitignored via logs/cronical*)
│   └── generate-ics-action.log    # written by GitHub Actions, committed to repo
├── public/                         # final output of calendar that is served
│   └── calendar.ics
├── .github/
│   └── workflows/
│       └── generate-ics-workflow.yml
├── cron-watcher.py                 # watches for crontab changes and pushes to GitHub
├── generate-ics.py                 # generates calendar.ics from all device files
├── setup.py                        # one-time setup script
├── sample-crons.txt                # sample cron jobs for testing
├── .env                            # local environment variables (never committed, created by setup.py)
├── .gitignore
├── pyproject.toml
├── .python-version
├── README.md
└── uv.lock
```

---

## Requirements

- `git` installed on your system
- Python 3.12+
- `uv` package manager ([install guide](https://docs.astral.sh/uv/getting-started/))
- A GitHub account with a Personal Access Token (PAT)

### Python Libraries

Managed via `pyproject.toml`:

```
cron-descriptor>=2.0.8
croniter>=6.2.2
icalendar>=7.1.0
python-crontab>=3.3.0
python-dotenv>=1.2.2
regex>=2026.5.9
```

---

## Using Your Own GitHub Repository

Create a new private repository on GitHub named `cronical`, then run:

```bash
git clone https://github.com/original-owner/cronical.git
cd cronical

git remote remove origin
git remote add origin https://github.com/yourusername/cronical.git

git push -u origin main
```

If your repository uses `master` instead of `main`, use:

```bash
git push -u origin master
```

You can then clone and use your personal repository normally.

---

## Quick Setup (Recommended)

```bash
# 1. Install dependencies
uv sync

# 2. Run the setup script
uv run setup.py
```

The setup script will:
- Check `git` is installed and `.venv` exists
- Create the `crons/`, `public/` and `logs/` directories
- Create your device file in `crons/`
- Copy your current crontab into the device file
- Add `cron-watcher.py` to your system crontab (runs every minute by default)
- Create and populate your `.env` file
- Ensure `.env`, `.venv/` and `logs/cronical*` are in `.gitignore`

All actions are logged to `logs/cronical.log`.

---

## Manual Setup

If you prefer to set up manually or want to understand what `setup.py` does:

### 1. Create a virtual environment and install dependencies

```bash
uv venv
source .venv/bin/activate
uv sync
```

### 2. Create required directories

```bash
mkdir -p crons public logs
```

### 3. Create a GitHub Personal Access Token (PAT)

- Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
- Click **Generate new token (classic)**
- Give it a name (e.g. `cronical`)
- Select scope: `repo` (full control of repositories)
- Copy the token immediately, GitHub will not show it again

### 4. Create your device cron file

```bash
# replace "laptop" with your device name
crontab -l > crons/laptop.txt
```

### 5. Create and fill in your `.env` file

```bash
DEVICE_NAME=laptop
DEVICE_PATH=/full/path/to/cronical/crons/laptop.txt
GITHUB_PAT=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_USER=yourusername
GITHUB_REPO_NAME=cronical
```

Never commit `.env` to git. It is already in `.gitignore`.

### 6. Add the watcher to your crontab

```bash
crontab -e
```

Add this line, replacing the path with your actual path. The watcher runs every minute by default but you can adjust the frequency to suit your needs:

```
* * * * * /path/to/cronical/.venv/bin/python /path/to/cronical/cron-watcher.py # cronical-watcher
```

### 7. Confirm `.gitignore` contains

```
.env
.venv/
logs/cronical*
```

---

## Adding a Second Device

On the new device:

```bash
git clone https://github.com/yourusername/cronical.git
cd cronical
uv sync
uv run setup.py
```

The setup script will create a new device file in `crons/` and configure the watcher. All devices push to the same repo and GitHub Actions merges them into one calendar.

---

## Scripts

### `setup.py`

One-time setup script. Run this after cloning the repo on any new device. Logs all actions to `logs/cronical.log`. It will:

- Check that `git` is installed and `.venv` exists
- Create `crons/`, `public/` and `logs/` directories
- Create your device file in `crons/`
- Copy your current crontab into the device file
- Add the watcher script to your system crontab (runs every minute)
- Create and populate your `.env` file
- Ensure `.env`, `.venv/` and `logs/cronical*` are in `.gitignore`

### `cron-watcher.py`

Runs as a cron job (every minute by default, configurable). Logs changes and git operations to `logs/cronical.log`. It will:

- Check all required `.env` variables are set
- Read your current crontab
- Compare it to your device file in `crons/`
- If changed: log the change, pull remote changes, update the device file, commit and push to GitHub
- If unchanged: print to terminal only, nothing written to log

### `generate-ics.py`

Runs in GitHub Actions on every push to `crons/**`. Logs progress to `logs/generate-ics-action.log`. It will:

- Read all device files from `crons/`
- For each job, determine if it runs multiple times per day:
  - If yes: one all-day event per active day
  - If no: one timed event per occurrence
- Save the merged `calendar.ics` to `public/`
- Log how many events were generated and where the file was saved

By default events are generated for 365 days ahead. If the ICS file becomes too large or calendar apps are slow to sync, you can reduce this by changing `HORIZON_DAYS` at the top of `generate-ics.py`:

```python
HORIZON_DAYS = 365  # reduce this if the file is too large
```

---

## Local ICS Generation (Alternative)

By default, `generate-ics.py` runs in GitHub Actions after each push. If you prefer to generate the calendar locally before pushing (for example, if you want to avoid relying on GitHub Actions entirely), `cron-watcher.py` includes a commented-out block that supports this:

```python
# run generate ics locally before adding, committing and pushing up instead of using github actions
# run_generate_ics_local()
# git_add()
# git_commit()
```

To enable local generation:

1. Uncomment the block above in `cron-watcher.py`
2. Comment out or remove the `git_push()` call that follows it, since the local flow does its own second commit and push
3. Optionally disable the GitHub Actions workflow entirely (delete or disable `.github/workflows/generate-ics-workflow.yml`)

In this mode the flow becomes:

```
crontab changes on your device
        ↓
cron-watcher.py detects the change
        ↓
updates the device file and commits it
        ↓
runs generate-ics.py locally to produce calendar.ics
        ↓
commits calendar.ics and pushes everything to GitHub
        ↓
calendar.ics is served from the repo directly
```

> [!WARNING]
> This is useful if you only have one device, want faster updates without waiting for Actions, or want to keep the repo fully self-contained without any CI dependency.

---

## Logging

`cron-watcher.py` and `setup.py` log to `logs/cronical.log`. `generate-ics.py` logs to `logs/generate-ics-action.log`. The format for all three is:

```
[2026-05-16 10:32:01] [setup]: Git is installed
[2026-05-16 10:32:02] [setup]: Device file created
[2026-05-16 10:32:03] [cron-watcher]: Cron jobs have changed, syncing...
[2026-05-16 10:32:04] [cron-watcher]: Repo pushed
[2026-05-16 10:32:05] [generate-ics]: Calendar saved to public/calendar.ics
```

`logs/cronical*` is gitignored. This covers the main log and all rotated backups (`cronical.log.1`, `cronical.log.2`, `cronical.log.3`). Log files rotate automatically at 1MB and up to 3 backups are kept.

`logs/generate-ics-action.log` is not gitignored and is committed to the repo by GitHub Actions after each run so you can inspect it without leaving GitHub.

To view local logs:
```bash
cat logs/cronical.log
# or follow live
tail -f logs/cronical.log
```

---

## Hosting

You have two options for hosting the `calendar.ics` file:

### Option 1: Public GitHub Repo + Raw URL (simplest, free)

If you are comfortable keeping your repo public (your crontab contents will be visible to anyone), you can use the raw GitHub URL directly with no extra setup needed:

```
https://raw.githubusercontent.com/yourusername/cronical/main/public/calendar.ics
```

### Option 2: Static Hosting Platform (private repo, public URL)

Keeps your repo private while serving the ICS file at a public URL. Cloudflare Pages works well for this:

1. Go to [pages.cloudflare.com](https://pages.cloudflare.com)
2. Connect your GitHub repo
3. Set the build output directory to `public`
4. No build command needed
5. Your ICS will be available at `https://your-project.pages.dev/calendar.ics`

You can also set a custom domain in Cloudflare Pages settings for free.

---

## How to Subscribe

Once you have your URL from either hosting option above:

### Google Calendar

1. Go to [calendar.google.com](https://calendar.google.com)
2. Click `+` next to **Other calendars**
3. Select **From URL**
4. Paste your URL and click **Add calendar**

### Apple Calendar

1. Open Calendar → File → New Calendar Subscription
2. Paste your URL and click Subscribe

### Outlook

1. Open Outlook → Add calendar → From internet
2. Paste your URL and click Import

---

## Resetting a Device

If you need to re-run setup on an existing device:

1. Delete your device file: `rm crons/devicename.txt`
2. Delete your `.env`: `rm .env`
3. Remove the watcher from crontab: `crontab -e` and delete the `# cronical-watcher` line
4. Run `uv run setup.py` again

---

## Limitations

- **Linux and macOS only.** Windows is not supported since it does not have a native cron daemon.
- **User crontab only.** System-wide crontabs in `/etc/cron.d/` or `/etc/crontab` are not monitored. Only the current user's crontab (`crontab -l`) is tracked.
- **Special cron syntax may not parse correctly.** Expressions like `@reboot` or non-standard syntax may be skipped or display incorrect human-readable descriptions.
- **Calendar events expire after 365 days by default.** The ICS regenerates on every crontab change, but if no changes happen for over a year, events will run out. Adjust `HORIZON_DAYS` in `generate-ics.py` if needed.
- **Google Calendar syncs slowly.** Google Calendar only refreshes subscribed calendars every 12-24 hours. Changes will not appear instantly.
- **Machine must be on.** If your machine is off or sleeping, the watcher cannot detect changes. Changes will sync the next time the machine is on and the watcher runs.
- **PAT expiry.** GitHub PATs can expire. If push/pull stops working, regenerate your PAT and update your `.env`.