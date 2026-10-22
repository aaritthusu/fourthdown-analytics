"""Refresh a public sports analytics site's data and model, safely.

GitHub Actions calls this script once each Tuesday. A successful download must not
remove previously published completed games, and an unchanged feed does not
trigger model training or a deployment. Never generate synthetic game results.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Allow running as `python scripts/weekly_refresh.py` from the repository root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.data import RAW_CACHE, clean, completed_games, refresh_data
from backend.modeling import train

MIN_FULL_SEASON_GAME_COUNT = 5000


def validate_new_data(previous: pd.DataFrame | None, updated: pd.DataFrame, now: datetime | None = None) -> dict:
    """Return verified counts, or fail closed on a truncated or stale feed."""
    now = now or datetime.now(timezone.utc)
    completed = completed_games(updated)
    if len(completed) < MIN_FULL_SEASON_GAME_COUNT:
        raise ValueError(f'Refusing incomplete schedule download: only {len(completed)} finished games')
    seasons = updated['season'].dropna()
    if seasons.empty:
        raise ValueError('No seasons were returned')
    # During the football season, do not accept a fallback source that has
    # dropped the current NFL season. Outside the season, last year's records
    # remain the newest legitimate season until the new schedule is released.
    required_season = now.year if now.month >= 9 else now.year - 1
    if int(seasons.max()) < required_season:
        raise ValueError(f'Schedule source is stale: newest season {int(seasons.max())}; expected at least {required_season}')

    previous_count = 0
    new_completed = len(completed)
    if previous is not None:
        prev_completed = completed_games(previous)
        previous_count = len(prev_completed)
        if new_completed < previous_count:
            raise ValueError(f'Completed-game count regressed: {previous_count} → {new_completed}')
        current_results = completed.set_index('game_id')
        missing = set(prev_completed['game_id']) - set(current_results.index)
        if missing:
            raise ValueError(f'Existing final games went missing or lost scores: {len(missing)}')
    return {
        'previous_finished_games': previous_count,
        'current_finished_games': new_completed,
        'newly_finished_games': max(0, new_completed - previous_count),
        'schedule_season': int(seasons.max()),
    }


def comparable_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Ignore incidental CSV serialization changes, but detect schedule edits."""
    normalized = frame.copy()
    # CSV parser versions may represent an integral score as 21 or 21.0.
    for column in ('away_score', 'home_score'):
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors='coerce').map(
                lambda value: '__MISSING__' if pd.isna(value) else format(float(value), '.10g')
            )
    return normalized.fillna('__MISSING__').astype(str).reset_index(drop=True)


def run() -> int:
    prior = clean(pd.read_csv(RAW_CACHE, low_memory=False)) if RAW_CACHE.exists() else None
    updated, source = refresh_data()  # Raises if both sources fail; never falls back silently.
    stats = validate_new_data(prior, updated)
    print(f"NFL data refresh: {json.dumps(stats)}", flush=True)
    if prior is not None and comparable_data(prior).equals(comparable_data(updated)):
        print('No schedule or result changes. Skipping unnecessary retraining and deployment.', flush=True)
        return 0

    report = train(refresh=False)
    if report.get('coverage') != 'complete source as downloaded':
        raise ValueError('Refusing to publish a model trained on partial data')
    if report.get('finished_regular_games') != stats['current_finished_games']:
        raise ValueError('Model report does not match the refreshed dataset')
    if report.get('test_games', 0) < 240:
        raise ValueError('Refusing to publish without a sufficiently large full-season test')

    print('Model trained and checked. Selected:', report['selected_model'], flush=True)
    print('2025-style holdout score (actual chosen test season):', report['test_season'], report['test'], flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
