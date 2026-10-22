# FOURTHDOWN ANALYTICS

**NFL game prediction & model evaluation platform** · Full-stack student engineering project

FourthDown Analytics is a runnable, source-available sports statistics experiment. It ingests **real NFL results**, constructs information-safe pregame statistics, trains and compares machine-learning models, saves out-of-sample predictions, exposes a Python API, and displays the results in a six-section React dashboard.

> **Read first:** The bundled demonstration data is a *verified but incomplete excerpt* of 205 finished NFL games plus 28 future schedule entries, checked against the nflverse game CSV on **October 21, 2026**. It is not a complete season archive. The model artifact is genuinely trained on this excerpt, but its probabilities and team records should **not** be considered scientifically representative until you perform the full download/retrain step. The UI explicitly warns when this limited data is loaded. This is statistical research, **not gambling or wagering advice**.

## Publish for everyone to visit

A deployment-ready `render.yaml` (FastAPI API), `.python-version` (Python 3.13), and production CORS configuration are included. Use **Render + Vercel** with your GitHub repository: see [`PUBLIC_DEPLOYMENT.md`](PUBLIC_DEPLOYMENT.md) for complete steps, environment variables, honest limits, and a launch checklist. A deployed URL works across devices independently of your PC. **No forecasting algorithm can guarantee perfect game predictions.**

## What is implemented

| Layer | What it does |
|---|---|
| Data | Downloads publicly accessible nflverse schedule CSVs, validates needed columns, canonicalizes team IDs, caches full data; works offline with clearly marked partial excerpt |
| Features | Season-to-date record, rolling 8-game scoring, scoring margin and 3-game form, game count, neutral/home venue; only earlier weeks feed each historical game |
| Training | Logistic regression, random forest, histogram gradient boosting, and an empirical home-win baseline; select by validation log loss and score held-out season once |
| Evaluation | Accuracy, precision, recall, confusion matrix, Brier score, log loss, five-bin calibration, experiment metadata, model version and saved test predictions |
| API | `/api/health`, `/api/overview`, `/api/teams`, `/api/compare`, `/api/predictions`, `/api/predict`, `/api/performance`, `/api/games`; validation, pagination, filtering |
| Web | Six responsive Next.js pages: Overview, Predictions, Team comparison, Model performance, Historical games, Methodology |
| Testing | Pytest feature-freezing/leakage tests, input validity, API health, score probability invariants; code and data provenance in repository |

The dashboard uses custom team badges rather than distributing copyrighted NFL logos. The frontend has loading, error, and empty states.

## Folder structure

```text
fourthdown-analytics/
├── backend/
│   ├── data.py             # fetch, cache, normalize schedule
│   ├── features.py         # before-kickoff feature engineering
│   ├── modeling.py         # chronological evaluation and saved model
│   └── main.py             # FastAPI endpoints
├── data/
│   └── verified_excerpt.csv # real but PARTIAL offline data
├── artifacts/
│   ├── model.joblib        # fitted model; regenerate after new data
│   ├── evaluation.json    # measured metrics + experiment metadata
│   └── backtest.csv       # saved holdout predictions
├── frontend/
│   ├── src/app/            # six routes and responsive CSS
│   ├── src/components/     # shared charts and UI
│   └── src/lib/            # API hook, types and team names
├── scripts/
│   ├── build_verified_excerpt.py
│   ├── audit_data.py
│   └── refresh.sh
├── tests/
├── requirements.txt
├── TECHNICAL_SUMMARY.md
├── DEPLOYMENT.md
└── README.md
```

## Start locally (Windows, Mac, or Linux)

Requires **Python 3.10+** and **Node.js 20+**, an internet connection for the initial installation, and two terminals. Extract this archive, and open the `fourthdown-analytics` folder.

### Terminal A — FastAPI + trained model

```bash
# In fourthdown-analytics/ (repository root)
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Optional: retrain on the bundled, explicitly partial offline dataset.
# A pre-trained artifact is already included for immediate API use.
python -m backend.modeling

# Run the HTTP API (docs at http://localhost:8000/docs)
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal B — Next.js dashboard

```bash
cd frontend
npm install
# Optionally create .env.local from .env.example.
# By default, the app contacts http://localhost:8000.
npm run dev
```

Open **http://localhost:3000**. Change model/data files only while the API is stopped, then restart it so its in-process cache reloads. For built frontend: `npm run build && npm run start`.

### Recommended: Refresh complete historical data

```bash
# Stop the FastAPI server, and run at repository root:
python -m backend.modeling --refresh
# Restart the backend.
```

This attempts the nflverse schedules release first, then a public GitHub raw CSV mirror. It downloads the entire historical NFL schedule, retains 2002 onward regular-season games, builds features from completed games, and retrains on the **eleven most recent seasons at most** when the full archive is present. No paid keys or credentials. **Do not use the partial offline metrics for a serious model claim.** If neither source is reachable, the refresh fails clearly instead of generating fictional data. Ordinary `python -m backend.modeling` will use the cached complete dataset once available.

Full source: https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv (primary) and https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv (fallback). Dataset attribution to **nflverse / nflverse-data**, under the datasets' CC BY 4.0 licensing. Check upstream release terms if redistributing adapted datasets.

## First-run metrics: **partial offline excerpt only**

Actual saved output in `artifacts/evaluation.json`, with unrounded raw probabilities for the historical test games in `artifacts/backtest.csv`. The experiment used **66** completed non-tied games in 2024 for initial training, **61** games in 2025 for algorithm selection, and **76** games in 2026 for the one-time test. **205** completed games in the excerpt, **203** usable binary outcomes (two ties excluded from training).

- Validation winner: **logistic regression** (chosen by validation log loss, not test accuracy).
- Held-out 2026 test: **57.9% accuracy**, **0.777 log loss**, **0.269 Brier score**.
- Home-win-frequency baseline: **50.0% accuracy**, **0.704 log loss**, **0.256 Brier score**.
- Therefore, the model performs *worse* than the baseline on probabilistic scoring, even though binary accuracy is higher. The excerpt is small, deliberately incomplete, and not representative of true model strength.
- Numbers were computed by `python -m backend.modeling` with scikit-learn; you can reproduce them from saved input CSV. Do not present them as full-season NFL results.

The scripts record the exact selected algorithm, dataset counts, chronological splits, test confusion matrix and calibration bins. `training_games + validation_games + test_games` represents the 203 non-tie games, not all schedule entries.

## Leakage protection and evaluation

1. Sort completed and uncompleted NFL games by season/week.
2. **Freeze the historical record before every week**: a game's features use only teams' results from *earlier* weeks, even if another game in the same week finished first.
3. Create home-minus-away comparisons for win rate, points scored/allowed, average margin, last-three margin and games observed. Add home/neutral field.
4. When the full download is used, exclude seasons older than a configurable modern horizon; never randomly interleave future games into training sets.
5. Assign earlier seasons to training, the penultimate season to validation and the latest season to test. Choose the model on validation log loss, refit on training + validation, and score the holdout **once**.
6. Save individual holdout predictions before refitting a **deployment** model on all observed games (the deployment model is *not* the holdout model). Historical pages display **saved holdout forecasts only**, never backfilled predictions from a model that saw the answer.
7. Predictions for an upcoming week only use earlier results. The API rejects historical ad hoc predictions, because generating them with the deployed model would leak future training information.

**Note:** Predictions include true, fitted model probabilities. For logistic regression, per-feature explanation values are actual additive contributions to predicted **log odds** after feature standardization. They are not SHAP values, causal effects or guarantees. For algorithms without this explanation, the display reverts to explicitly labeled raw matchup differences.

## API reference

The Swagger UI at `http://localhost:8000/docs` lists parameters and types. Examples:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/overview
curl http://localhost:8000/api/predictions
curl 'http://localhost:8000/api/predict?home=KC&away=BUF&season=2026&week=7'
curl 'http://localhost:8000/api/compare?home=KC&away=BUF'
curl 'http://localhost:8000/api/games?season=2026&week=6&result=final&limit=25'
curl http://localhost:8000/api/performance
```

The example week is for the October 21, 2026 data snapshot; use a **future** season/week after refreshing. Team IDs use nflverse conventions (`KC`, `BUF`, `LA`, `LAC`, `LV`, `WAS` etc.). For valid requests, the forecast payload includes team win probabilities summing to one, version hash, cutoff, model explanation and data coverage flag. HTTP 422 means an invalid combination of team IDs or an attempt to use a future-trained model for a historical fixture.

## Test the project

```bash
python -m pytest -q
python scripts/audit_data.py
# Typecheck Next.js after npm install:
cd frontend && npm run lint
# Check production bundle:
npm run build
```

The backend was executed and all **10 Python tests** passed in the project-creation environment, including leakage, model artifact, probability and API tests. The frontend source was created but **its npm dependencies could not be installed in the authoring sandbox** (DNS `EAI_AGAIN`); the web production build was therefore **not verified there**. On your own machine with internet, run `npm install`, `npm run lint`, and `npm run build`. This limitation is recorded rather than pretending that a browser build was verified.

## Technical constraints and responsible interpretation

- nflverse schedule data **does not** by itself provide injury reports, player playtime, yards, third-down conversions, EPA, QB context, or roster stability. No unsupported feature is silently invented.
- Incomplete excerpts distort rankings, past win rates and model reliability. Full refresh is essential for credible research.
- Teams can tie; ties affect team records but have no binary win/loss training label.
- Fresh schedule data can show upcoming fixtures with no outcomes. Future matchups in the current data are model probabilities, not actual results.
- There are no accounts, paid services, betting lines, or hidden API secrets.

## Portfolio-ready next experiments

Run repeated rolling-origin season folds (not just one validation/test), compare calibrated probabilities and simple baselines, add properly dated play-by-play efficiency data, measure confidence/calibration drift and build a documented ablation study. Do not report unverified gains. Consult `TECHNICAL_SUMMARY.md` for the honest project description and `DEPLOYMENT.md` for Vercel/Render/container notes.

## Credits

Independent educational development. **Source data:** nflverse schedules/results. **Tools:** pandas, NumPy, scikit-learn, joblib, FastAPI, Next.js, TypeScript, React, Recharts, Tailwind CSS, Lucide.
