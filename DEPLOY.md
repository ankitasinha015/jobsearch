# Deploying Job Radar to the internet (Render.com)

The dashboard runs anywhere; your private data does not live in git, so a
fresh deployment needs two secrets and one paste-in setup step.

## One-time setup (~10 minutes)

1. **Create a Render account** at https://render.com (sign in with GitHub).
2. **New + → Blueprint** → select the `ankitasinha015/jobsearch` repo.
   Render reads `render.yaml` and proposes the `job-radar` web service with a
   1 GB persistent disk (Starter plan, ~$7/month — required so the database
   and your profile survive restarts).
3. When prompted for environment variables, set the two secrets:
   - `ANTHROPIC_API_KEY` — same key as in your local `.env`
   - `RADAR_PASSWORD` — pick a strong password; the whole site is locked
     behind it (username `ankita`)
4. Deploy. First build takes a few minutes.
5. Open the app URL (something like `https://job-radar.onrender.com`),
   enter the username/password, and you'll see a **"One-time setup"** notice —
   open **Settings**, paste in the contents of your local `profile.md` and
   `preferences.yaml`, save.
6. Click **Run scan now**. Done — the daily scan then runs automatically at
   7:30 AM Pacific on the server, laptop on or off.

## What's different from the laptop version

- Auth: HTTP Basic (`RADAR_PASSWORD`) protects every page.
- Data: lives on the Render disk at `/data` (`RADAR_DATA_DIR`).
- Scheduler: in-process daily scan (`RADAR_SCHEDULER=1`) instead of Windows
  Task Scheduler.
- JobSpy aggregators are off by default in cloud (`RADAR_JOBSPY=0`) — cloud
  IPs get blocked quickly; the 44 ATS boards are unaffected.
- Dispositions/history start fresh in the cloud (the laptop `radar.db` is not
  uploaded). If you want the laptop history migrated, copy `radar.db` to the
  server disk once via Render's shell.

## Running both

Keep the laptop setup as a backup or turn off its Task Scheduler job
(`JobRadarDailyScan`) to avoid double scanning costs. Both write to their own
separate databases; pick one as the daily driver.
