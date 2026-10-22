from datetime import datetime, timezone
import pandas as pd
import pytest

from scripts.weekly_refresh import validate_new_data, comparable_data


def fake_schedule(n, season=2026, completed=True):
    return pd.DataFrame({
        'game_id':[f'{season}_{i}' for i in range(n)],
        'season':[season]*n,
        'week':[1+i%18 for i in range(n)],
        'home_score':[20 if completed else None]*n,
        'away_score':[13 if completed else None]*n,
    })


def test_missing_or_truncated_source_is_rejected():
    with pytest.raises(ValueError,match='incomplete'):
        validate_new_data(None, fake_schedule(300),datetime(2026,10,22,tzinfo=timezone.utc))


def test_complete_source_passes_validation():
    result=validate_new_data(None, fake_schedule(5100),datetime(2026,10,22,tzinfo=timezone.utc))
    assert result['current_finished_games']==5100


def test_removed_final_games_fail_closed():
    old=fake_schedule(5003)
    updated=old.iloc[1:].copy()
    with pytest.raises(ValueError,match='regressed'):
        validate_new_data(old,updated,datetime(2026,10,22,tzinfo=timezone.utc))


def test_stale_current_season_rejected():
    with pytest.raises(ValueError,match='stale'):
        validate_new_data(None,fake_schedule(5100,season=2025),datetime(2026,10,22,tzinfo=timezone.utc))


def test_csv_dtypes_do_not_trigger_retraining():
    a=pd.DataFrame({'home_score':[21.0,None], 'away_score':[14.0, None]})
    b=pd.DataFrame({'home_score':[21,None], 'away_score':[14,None]})
    assert comparable_data(a).equals(comparable_data(b))


def test_browser_title_and_navigation_credit_creator():
    from pathlib import Path
    project_root=Path(__file__).resolve().parents[1]
    layout=(project_root/'frontend/src/app/layout.tsx').read_text()
    nav=(project_root/'frontend/src/components/UI.tsx').read_text()
    assert 'FourthDown Analytics — Created by Aarit Thusu' in layout
    assert 'BY AARIT THUSU' in nav
    assert 'Created and developed by' in (project_root/'frontend/src/app/page.tsx').read_text()


def test_weekly_automation_does_not_commit_experimental_artifacts():
    from pathlib import Path
    workflow=(Path(__file__).resolve().parents[1]/'.github/workflows/weekly-nfl-refresh.yml').read_text()
    assert 'workflow_dispatch:' in workflow
    assert "17 17 * * 2" in workflow
    assert 'data/nfl_games.csv' in workflow
    assert 'artifacts/model.joblib' in workflow
    assert 'artifacts/research_report.json' not in workflow
