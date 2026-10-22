# FourthDown Analytics — Trends & Accuracy Research Upgrade

This release changes the visual design, adds an evidence-backed Trends page, and provides a stronger **candidate research pipeline**. It does **not** promise perfect predictions or secretly change the production model. The bundled 205-game excerpt remains incomplete until you refresh from nflverse.

## What's new

- `/trends`: choose any NFL team, optionally filter opponent and venue, and compare the last 3, 5, 8, 10, 15 or 20 **available completed games**.
- Win streaks, close games, double-digit wins, points scored, points allowed, total combined scoring, venue-specific results, and head-to-head trends.
- The sample count, denominator, and completed game IDs/scores accompany every claim. When data is incomplete, the page says so. Trends are descriptions, not future-win guarantees.
- Editorial charcoal-and-copper design: flat surfaces, muted colors, restrained typography and copy; no neon glow.
- `/api/trends`, `/api/research`, 7 additional Python tests.
- `backend/research.py`: leakage-safe Elo, rest, recent margin, venue form and historical opponent-quality features, plus up to 4 chronological full-season test folds and comparison of basic and enhanced models.
- `backend/modeling.py` avoids using an in-progress season as the main **full-season** test once complete nflverse games have been loaded.

## Update your existing GitHub repository (Windows)

Your public services already deploy from GitHub. **Do not create new Vercel or Render projects.**

1. Install GitHub Desktop from the official site `https://desktop.github.com/` if needed; sign in to the GitHub account that owns `fourthdown-analytics`.
2. Choose **File → Clone repository → fourthdown-analytics** and select an easy-to-find local destination. Do not clone into the folder containing another repository.
3. Unzip this release, open its inner `fourthdown-analytics` folder and **copy its contents** into the cloned repository folder, replacing matching files. Do not copy the inner folder itself. Do not copy `.venv`, `node_modules` or private configuration.
4. In GitHub Desktop, review changed files. The new Python research code and trends page should show up. Commit with a descriptive message and click **Push origin**.
5. GitHub pushes normally trigger your existing Vercel frontend and Render backend deployments. The Trend page will work on the existing excerpt, but will clearly label it incomplete.
6. Check `https://fourthdown-analytics.vercel.app/trends` and `https://fourthdown-analytics-api.onrender.com/api/trends?team=KC&last=5`. Confirm all 6 navigation pages still work.

## Refresh the full schedule and retrain with real data

Do this on the **cloned repository on your computer** (Python 3.13, not Python 3.15). In PowerShell from its project root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m backend.modeling --refresh
.\.venv\Scripts\python.exe -m backend.research
.\.venv\Scripts\python.exe -m pytest -q
```

Or, after installation, use `powershell -ExecutionPolicy Bypass -File scripts/refresh_models.ps1`.

The first refresh fetches schedules/results from nflverse. It requires an internet connection on **your** computer. If the download fails, do not synthesize results or copy invented numbers into the CSV. Retry after the source is available.

The model script writes or updates:

- `data/nfl_games.csv` — the full source schedule cache (tracked to preserve model/data compatibility on Render).
- `artifacts/model.joblib` — production model trained and scored from complete games; note that model selection may still produce disappointing accuracy.
- `artifacts/evaluation.json` — actual held-out performance, with last completed regular season as the full-season test.
- `artifacts/backtest.csv` — the holdout predictions.

The research script writes `artifacts/research_report.json` with per-year, out-of-sample comparisons of basic vs enhanced candidates. **This is a research report, not an automatically promoted model.** It requires multiple complete seasons; the bundled partial excerpt is deliberately rejected.

Once both commands finish, inspect the reports. In GitHub Desktop, commit and push `data/nfl_games.csv` plus all updated artifacts and code together. Render redeploys the exact source data used for the saved model. Vercel redeploys the website.

### Why no automatic model upgrade?

A complicated algorithm can look better on training data and be worse on new seasons. This project's challenger experiment compares future-season accuracy **and** the Brier score and log loss. We intentionally do not choose a challenger on the same held-out test seasons and then claim those seasons are a fresh independent final test. Promotion requires a separate unseen period and an explicit change to the inference pipeline. Never present a reported validation improvement as a proven production accuracy gain.

### Data and licensing

Schedule/results source: [nflverse](https://github.com/nflverse/nflverse-data) and [nflverse nfldata](https://github.com/nflverse/nfldata). NFL game data in this project is attributed to nflverse under CC BY 4.0. Ensure you review the upstream dataset's license and update schedule before distribution.

This independent research project does not incorporate betting advice or predictions of certainty.
