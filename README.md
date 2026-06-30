# My Internship Feed — auto-updating tracker of open postings

This is a small tool that, every day, pulls live internship postings from public job-tracker repos, keeps only **your** target companies (listed in `targets.txt`), and writes the result to:

- `output/internships.csv` — open it in Excel/Sheets, or import into your main tracker
- `output/internships.html` — a clean page you can open in any browser

It runs **by itself once a day** in the cloud (free) via GitHub Actions. After a ~5-minute one-time setup, you never touch it again.

---

## One-time setup (~5 minutes)

You need a free GitHub account. Then:

1. **Create a new repository.** On github.com, click the **+** (top right) → **New repository**. Name it anything (e.g. `internship-feed`). Set it to **Public** (free Actions) or Private (also fine on free tier). Click **Create repository**.

2. **Upload these files.** On the new repo page, click **uploading an existing file** (or **Add file → Upload files**). Drag in everything from this folder, keeping the structure:
   - `fetch_internships.py`
   - `targets.txt`
   - `output/` (the folder, with its two files)
   - `.github/workflows/update.yml`  ← important: this path must be exact
   Then **Commit changes**.
   - Note: GitHub's web uploader can be finicky about folders. If the `.github/workflows/update.yml` path doesn't upload cleanly, use **Add file → Create new file**, type `.github/workflows/update.yml` as the name (the slashes create the folders), and paste the contents of that file in.

3. **Enable Actions write access.** In your repo: **Settings → Actions → General → Workflow permissions** → select **Read and write permissions** → **Save**. (This lets the daily job commit the updated files back.)

4. **Run it once now.** Go to the **Actions** tab → click **Update internship feed** → **Run workflow** → **Run workflow**. Wait ~1 minute. It will refresh `output/internships.csv` and `output/internships.html`.

That's it. From now on it runs automatically every day at 13:00 UTC.

---

## How to use it day to day

- Open `output/internships.html` for a quick read of which of your targets are open right now (with direct apply links).
- Or open `output/internships.csv` and copy rows/deadlines into your main tracker spreadsheet.
- Want a live web link? In **Settings → Pages**, set the source to your main branch `/root` (or move the html to a `docs/` folder), and GitHub gives you a URL that always shows the latest feed.

## Editing your targets

Open `targets.txt` and add/remove company match-terms (one per line, `#` comments ignored). Use the shortest distinctive token. The next daily run picks up your changes — or trigger it manually from the Actions tab.

---

## Honest limitations (so nothing surprises you)

- **It only shows companies that currently have an open posting in the source repos.** Most of your targets only appear when they open applications (typically fall, for the next summer). An empty or short list in, say, spring is normal — it is not broken.
- **Frontier labs (OpenAI, Anthropic, etc.) mostly recruit on their own sites** and often do **not** appear in these repos. No script fixes that; the data isn't there. Check those companies' career pages directly.
- **The sources are community-maintained.** If a repo changes its format or moves, a source may stop returning rows (the script skips it and notes it; the other sources still work). When you actually apply in **fall 2027**, update the repo year in the `SOURCES` list at the top of `fetch_internships.py` to the then-current cycle (e.g. `2028`).

## Run it locally (optional)

No installs needed (standard library only):

```
python fetch_internships.py
```

It writes the two files into `output/`. This is also how you'd test changes to `targets.txt` before committing.

---

*Built as a companion to the micro1 Master Handbook and the internship tracker. This is also a legitimate portfolio project: a scheduled data pipeline that fetches, parses, filters, and publishes — exactly the kind of small, real, end-to-end system worth showing on a resume.*
