"""All enriched features must be frozen before game-week outcomes."""
import numpy as np
import pandas as pd
import pytest
from backend.data import clean
from backend.features import build_features
from backend.research import augment_features,ADDITIONAL,study


def sample():
    return clean(pd.DataFrame([
        {'game_id':'2023_01_KC_BUF','season':2023,'game_type':'REG','week':1,'home_team':'BUF','away_team':'KC','home_score':10,'away_score':20,'gameday':'2023-09-07'},
        {'game_id':'2023_01_LV_DEN','season':2023,'game_type':'REG','week':1,'home_team':'DEN','away_team':'LV','home_score':40,'away_score':10,'gameday':'2023-09-10'},
        {'game_id':'2023_02_KC_DEN','season':2023,'game_type':'REG','week':2,'home_team':'DEN','away_team':'KC','home_score':25,'away_score':22,'gameday':'2023-09-17'},
        {'game_id':'2023_03_KC_DEN','season':2023,'game_type':'REG','week':3,'home_team':'DEN','away_team':'KC','home_score':None,'away_score':None,'gameday':'2023-09-24'},
    ]))


def test_same_week_results_do_not_change_advanced_features():
    original=sample()
    before=augment_features(original)
    altered=original.copy()
    altered.loc[altered.game_id=='2023_01_LV_DEN','home_score']=1000
    after=augment_features(altered)
    for gid in ['2023_01_KC_BUF','2023_01_LV_DEN']:
        a=before[before.game_id==gid][ADDITIONAL].iloc[0].values
        b=after[after.game_id==gid][ADDITIONAL].iloc[0].values
        assert np.allclose(a,b)
    assert not before[ADDITIONAL].isna().any().any()


def test_changing_future_week_cannot_change_earlier_features():
    base=sample()
    before=augment_features(base)
    alt=base.copy()
    alt.loc[alt.game_id=='2023_02_KC_DEN','home_score']=100
    after=augment_features(alt)
    for gid in ['2023_01_KC_BUF','2023_01_LV_DEN','2023_02_KC_DEN']:
        assert np.allclose(before[before.game_id==gid][ADDITIONAL],after[after.game_id==gid][ADDITIONAL])


def test_partial_excerpt_rejected_for_accuracy_claims(monkeypatch):
    # Explicitly supply partial data so this test remains valid even when a
    # developer has downloaded the full nflverse cache locally.
    import backend.research as research
    monkeypatch.setattr(research, 'load_data', lambda refresh=False: (sample(), 'PARTIAL verified excerpt'))
    with pytest.raises(ValueError, match='complete seasons'):
        research.study()
