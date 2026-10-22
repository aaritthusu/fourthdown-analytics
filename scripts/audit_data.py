"""Check integrity and coverage of currently cached NFL data and saved artifacts."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from backend.data import load_data,completed_games
from backend.features import build_features,FEATURE_NAMES
from backend.modeling import REPORT,ARTIFACT,BACKTEST


def audit():
    games,source=load_data()
    assert len(games)>=100, 'Too few games'
    assert games.game_id.is_unique, 'Duplicate game IDs'
    assert games.away_team.ne(games.home_team).all(), 'Same team both sides'
    assert games.week.between(1,18).all(), 'Week out of range'
    assert games.season.ge(2002).all(), 'Unexpected season'
    missing_one=games.home_score.isna() != games.away_score.isna()
    assert not missing_one.any(), 'Partial score present: one team has no score'
    assert games[['home_score','away_score']].dropna().ge(0).all().all(), 'Negative game score'
    feat,history=build_features(games)
    assert len(feat)==len(games),'Feature rows missing'
    assert not feat[FEATURE_NAMES].isna().any().any(), 'Missing model features'
    assert all((feat.loc[feat['season']==g.season].week>=1).all() for _,g in games.head(1).iterrows())
    report=json.loads(REPORT.read_text()) if REPORT.exists() else None
    if report:
        assert ARTIFACT.exists(),'Evaluation report but no serialized model'
        assert BACKTEST.exists(),'Evaluation report but no historical backtest'
        bt=pd.read_csv(BACKTEST)
        assert bt.home_win_probability.between(0,1).all(), 'Invalid saved probabilities'
        assert len(bt)==report['test_games'],'Saved backtest count mismatch'
        if len(games)==report['rows_total']:
            assert len(completed_games(games))==report['finished_regular_games'],'Training artifacts do not match source game count'
    print(json.dumps({'records':len(games),'completed':len(completed_games(games)),
          'seasons':sorted(games.season.unique().tolist()),'partial': 'PARTIAL' in source,
          'model_artifact':ARTIFACT.exists(),'saved_predictions':int(report['test_games']) if report else 0,
          'integrity':'PASS'},indent=2))

if __name__=='__main__':
    audit()
