# FourthDown Analytics: publish the website (Render + Vercel)

A public site needs **two cloud apps**: a Python FastAPI backend and a Next.js frontend. The hosted site stays available without running PowerShell on your own PC (subject to host uptime and free-tier limitations).

**This repository is a school-project demonstration.** The included trained model uses an incomplete 205-game extract; it is **not** a reliable forecasting system. A public launch must clearly label its partial coverage. For materially meaningful forecasts, refresh nflverse and retrain first, evaluate on a later season, and redeploy the matched data + model files. No NFL predictor can promise perfect outcomes.

## 1. Put the source on GitHub

1. Extract this ZIP (there is one `fourthdown-analytics/` folder inside the ZIP).
2. At <https://github.com/new> create a repository, e.g. `fourthdown-analytics`. This may be private or public. If public, don't commit personal information or secret credentials.
3. On the repository page choose **Add file → Upload files**. Upload the **contents** of the `fourthdown-analytics` project folder (not the outer ZIP). GitHub's web upload is not convenient for nested folder structures; GitHub Desktop / `git push` are more reliable, see commands below.
4. Recommended: install **GitHub Desktop** (<https://desktop.github.com/>) and add the extracted folder as a local repository, then **Publish repository**. The `.gitignore` already excludes local virtual environments, `node_modules`, and personal frontend environment files.
5. Verify the repo's root contains `backend/`, `frontend/`, `requirements.txt`, and `render.yaml`.

Alternatively, from the project root (Git installed):

```bash
git init
git add .
git commit -m "Initial FourthDown Analytics"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fourthdown-analytics.git
git push -u origin main
```

Create the empty GitHub repo first; replace YOUR_USERNAME. Authentication to GitHub must be completed in the browser or with a credential manager; do not paste credentials into chat.

## 2. Publish the FastAPI backend on Render

1. Go to <https://dashboard.render.com/>, sign in, and connect your GitHub repo.
2. Choose **New → Blueprint**, select the repository, and approve the `render.yaml` service configuration. Alternatively choose **New → Web Service**, root **repository root**, runtime **Python**, free plan for a demonstration, build `pip install -r requirements.txt`, start `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
3. Render's public service URL looks like `https://YOUR-API.onrender.com`; save your **actual** URL (don't copy the example). Visit `https://YOUR-API.onrender.com/api/health` and make sure `ok` and `model_loaded` are `true`.
4. Under Render **Environment**, ensure `PYTHON_VERSION` is `3.13.5` (included in `render.yaml`).

**Free-tier caution:** Render's free web services may go to sleep after 15 minutes idle and can take about one minute to spin up; this is not true always-on hosting. Their filesystem also does not persist writes across service restarts/deploys. The included demo model and data are already in the deployed repository, so they can load without an internet fetch.

## 3. Publish the Next.js website on Vercel

1. Go to <https://vercel.com/new>, import the **same** GitHub repository.
2. Set **Root Directory** to `frontend` (not the repository root). Framework: **Next.js**.
3. In **Environment Variables**, add the exact name `NEXT_PUBLIC_API_BASE_URL` with value equal to your Render **HTTPS** URL, e.g. `https://YOUR-API.onrender.com` (no `/api` suffix or trailing slash).
4. Deploy; Vercel provides a public `https://...vercel.app` link. Copy the exact main production URL.
5. IMPORTANT: return to your **Render API > Environment** and create/set `FRONTEND_ORIGINS` to your exact frontend origin, e.g. `https://YOUR-SITE.vercel.app` (no trailing slash or path). Save and redeploy the Render service.
6. In Vercel redeploy if you changed the `NEXT_PUBLIC_API_BASE_URL` variable after the initial build (public Next.js environment variables are set at build time).
7. Open the public Vercel URL in a private browser window or on another device. Go to Overview, Predictions, Team Comparison, Performance and Historical Games. The user does **not** need to run your PC.

## 4. Verify your deployment (critical)

- `https://YOUR-API.onrender.com/api/health` should return JSON including `"ok": true`, `"model_loaded": true`.
- `https://YOUR-API.onrender.com/api/overview` should return real records and report `"partial_coverage": true` until the full retraining is deployed.
- The Vercel website should show actual API numbers; if it shows `Failed to fetch`, verify `NEXT_PUBLIC_API_BASE_URL` and `FRONTEND_ORIGINS` **and redeploy the affected service**.
- In Chrome DevTools > Network, requests to `...onrender.com/api/...` should succeed without CORS errors.
- Check on mobile/cellular so the test is **not** accidentally using localhost.

## 5. Make the model scientifically stronger (not perfect)

The included demo excerpt is small and incomplete. Before publicizing forecasts as research conclusions:

```bash
# On your local machine, at the repository root, after Python setup:
.venv/Scripts/python.exe -m backend.modeling --refresh  # Windows PowerShell
# OR: python -m backend.modeling --refresh
python -m pytest -q
```

This downloads the complete source schedule, builds pregame-only features, compares algorithms on a later validation season, evaluates on a separate holdout season, and writes `data/nfl_games.csv` plus refreshed `artifacts/` files. Make sure the generated complete data and the updated model artifacts are **deployed together**, and credit nflverse (check dataset licensing and attribution requirements).

The `data/nfl_games.csv` file is ignored by default in `.gitignore` to keep local cache out of the repository. If you choose to bundle a verified complete snapshot for hosting, remove that one `.gitignore` entry or `git add -f data/nfl_games.csv`, then commit the CSV **with** the new model and evaluation artifacts. Do not deploy a newly trained model with the old demo CSV: the API intentionally detects mismatched data hashes.

If the chronological holdout accuracy, log loss, or Brier score is weak, report those results and iterate; do not invent confidence or accuracy numbers. For further work, add prior-week EPA/play-by-play aggregation, injuries and expected starters with timestamp-verified sources, stronger calibration, and multiple season walk-forward backtests. Each new feature must be known **before kickoff**.

## Free vs dependable public hosting

- Render Free and Vercel Hobby are suitable for a non-commercial school demo and have usage/eligibility limits. Vercel Hobby is restricted to personal non-commercial usage.
- For a widely used, always-responsive site you may need a paid API instance; prices and platform policies can change.
- A custom domain is optional, not required: Render/Vercel provide public HTTPS links automatically.

Helpful official sources:
- <https://render.com/docs/deploy-fastapi>
- <https://render.com/docs/free>
- <https://render.com/docs/blueprint-spec>
- <https://vercel.com/docs/monorepos>
- <https://vercel.com/docs/plans/hobby>
- <https://github.com/nflverse/nflverse-data>
