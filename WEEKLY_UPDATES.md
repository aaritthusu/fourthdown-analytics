# Weekly NFL updates (GitHub Actions)

Created and developed by **Aarit Thusu**.

This project refreshes schedule data and forecasts **without leaving your PC on**. A workflow checks the latest nflverse data each Tuesday at **17:17 UTC** (1:17 p.m. Eastern during daylight saving time / 12:17 p.m. during standard time). NFL results are third-party data: a scheduled check does not guarantee that every delayed or corrected game has already appeared.

## One-time setup

1. Copy the patch's `.github`, `frontend`, `backend`, `scripts`, `tests` files into your **existing GitHub Desktop clone**, merging folders and replacing matching source files. **Do not replace `data/` or `artifacts/`.** The patch deliberately leaves your trained model and 6,316-game download untouched.
2. In GitHub Desktop, review changes, **Commit to main**, and **Push origin**.
3. On GitHub, open `AaritTheGreat/fourthdown-analytics` → **Actions** → **Weekly NFL data and model refresh** → **Run workflow** → select `main` → **Run workflow** once to test. If GitHub asks you to enable Actions, enable them for this repository.
4. When the run shows a green check, open its logs and confirm that data was checked, the tests ran, and any changes were committed. On later Tuesdays this happens automatically.
5. In Render → **fourthdown-analytics-api → Settings**, ensure **Auto-Deploy: On Commit**. Render should deploy updated commits automatically; check the service's Events page. Vercel will remain connected to the same repository.
6. Check your public [dashboard](https://fourthdown-analytics.vercel.app) and [API status](https://fourthdown-analytics-api.onrender.com/api/health). The dashboard shows the trained-model date when it has been updated.

## How it works

- Downloads actual `games.csv` from nflverse; rejects download errors rather than silently using a sample.
- Confirms the feed still includes **5,000+ completed regular-season games** and does not remove any previously published completed game.
- On real schedule/result changes, recomputes pregame features, trains the model with chronological validation, and runs unit tests.
- Commits **only** `data/nfl_games.csv`, `artifacts/model.joblib`, `artifacts/evaluation.json`, and `artifacts/backtest.csv` to `main`.
- If there are no meaningful data changes, skips training and the deployment.
- On errors, the workflow fails **without replacing production files**. Check the GitHub Actions logs and fix the problem before manually retrying.

## Operating notes

- This pipeline ingests and models **regular-season games only**. Playoff game forecasting is not included. Predictions are **weekly statistical estimates, never guaranteed outcomes**. The test accuracy displayed on the site refers to a completed historical holdout season, not the current NFL week's forecast accuracy.
- For football data, nflverse currently documents frequent game/schedule updates. The source is credited in the site footer.
- GitHub states that scheduled workflows can be delayed, and that public-repository schedules may be disabled after 60 days of repository inactivity. Check that Actions remain enabled at the beginning of each football season. You can manually run the workflow at any time.
- GitHub Actions needs repository permissions to push (`contents: write` is included in the workflow). If you have branch protection or restrictive Actions policy, adjust your repository settings or use a reviewed pull-request release process.
- The script intentionally does **not** promote the experimental enhanced random forest. Keep that separate until independent verification.

## Verify new results

After a successful Tuesday update, compare the public `/api/overview` game counts, season and model version with the latest `artifacts/evaluation.json` committed by GitHub Actions. The model may reselect an algorithm based on that pipeline's validation results; never label a new model more accurate before evaluating it on later games.
