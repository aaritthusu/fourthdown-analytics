# FourthDown Analytics — Technical Project Summary

## What was actually built

FourthDown Analytics is a **Python/FastAPI + Next.js/React** NFL matchup analytics platform with an actual machine-learning backend. The code loads real schedule data, produces pregame-only team features, trains and compares three scikit-learn models, writes model artifacts and a held-out prediction CSV, and serves these results to six interactive dashboard pages. It is a reproducible student engineering exercise, not an NFL team/scouting product or wagering tool.

### Data

- Upstream data: public nflverse `games.csv` schedules and finished scores. No fake scores or generated probability inputs.
- Bundled source-verified **offline excerpt** checked October 21, 2026: 233 records total, 205 scored games, 28 upcoming games, across 2024–2026. This was transcribed from actual source records for offline demonstration and is **not complete**.
- The program can download an entire NFL historical games dataset when internet is available. Training is rerun on downloaded real records; no paid API keys are necessary.
- Supported fields: date/time (where available), team codes, game scores, season/week and neutral location. Supported features: season win rate, last eight-game points scored/allowed, overall and last-three scoring margin, games played, and home field. All inputs are calculated from completed *earlier weeks only*.

### Actual experiments

- **Training:** 2024 excerpt, 66 completed non-tied games.
- **Model selection:** 2025 excerpt, 61 completed non-tied games.
- **Final holdout:** 2026 excerpt, 76 completed non-tied games. Test was not used to choose the model.
- **Models compared:** standardized logistic regression, random forest, histogram gradient boosting and a simple home-win-frequency baseline.
- **Selected on validation log loss:** logistic regression.
- **Actual holdout results:** 57.9% accuracy; 0.777 log loss; 0.269 Brier score.
- **Actual baseline:** 50.0% accuracy; 0.704 log loss; 0.256 Brier score.
- **Interpretation:** The trained model is *not demonstrably well calibrated* and is **worse on proper probability-scoring metrics than the baseline**. With this partial, nonrepresentative excerpt, no performance claim beyond the actual limited test is warranted.
- **Reproducibility:** `artifacts/evaluation.json` contains machine-computed metrics and experiment metadata. `artifacts/backtest.csv` stores individual held-out probabilities and results. `artifacts/model.joblib` stores the separately refit deployment model.

### Engineering / implementation

- FastAPI endpoints with validation, season/team/week/status filters, pagination and user-facing errors.
- React/TypeScript app: dashboard, upcoming predictions, team comparison, measured model performance, historical game browser and methods page.
- Probability bars, team difference charts, feature explanations, calibration plot, confusion matrix, model version/cutoff annotations, and accessible data-coverage warnings.
- Input checks and tests for same-week/future leakage; model predictions and historical evaluation are separate.
- Offline fallback dataset is intentionally labeled as incomplete, never silently substituted for full results.

### Areas to improve next

1. Fetch full nflverse schedules with live network access and rerun the chronological experiment.
2. Perform multi-season rolling-origin validation and strength-of-schedule adjustments.
3. Add only genuinely sourced, pregame-available advanced team and player statistics, with accurate timestamping and missingness checks.
4. Evaluate feature ablations, additional calibration methods and season-based drift.
5. Record experiment outcomes in versioned reports, including cases when complexity lowers performance.

**Disclosure:** Backend training, API responses, and Python automated tests were run successfully. The author's environment could not fetch npm packages, so the Next.js build was not browser-verified there. Follow README setup/verification commands on your computer.
