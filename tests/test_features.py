import pandas as pd
import pytest
from backend.data import clean
from backend.features import build_features,FEATURE_NAMES,vector


def sample():
    return clean(pd.DataFrame([
        {'game_id':'2023_01_A_B','season':2023,'game_type':'REG','week':1,'away_team':'A','home_team':'B','away_score':10,'home_score':20,'gameday':'2023-09-10'},
        {'game_id':'2023_01_B_C','season':2023,'game_type':'REG','week':1,'away_team':'B','home_team':'C','away_score':50,'home_score':20,'gameday':'2023-09-11'},
        {'game_id':'2023_02_A_C','season':2023,'game_type':'REG','week':2,'away_team':'A','home_team':'C','away_score':31,'home_score':12,'gameday':'2023-09-17'},
        {'game_id':'2023_03_B_A','season':2023,'game_type':'REG','week':3,'away_team':'B','home_team':'A','away_score':None,'home_score':None,'gameday':'2023-09-24'},
    ]))


def test_future_score_cannot_change_past_features():
    frame=sample(); before,_=build_features(frame)
    after_data=frame.copy();after_data.loc[after_data.game_id=='2023_02_A_C','home_score']=1000
    after,_=build_features(after_data)
    for gid in ['2023_01_A_B','2023_01_B_C','2023_02_A_C']:
        assert (before.loc[before.game_id==gid,FEATURE_NAMES].values==after.loc[after.game_id==gid,FEATURE_NAMES].values).all()


def test_same_week_games_do_not_leak():
    features,_=build_features(sample())
    a=features[features.game_id=='2023_01_A_B'][FEATURE_NAMES].iloc[0]
    b=features[features.game_id=='2023_01_B_C'][FEATURE_NAMES].iloc[0]
    assert a['point_diff_difference']==0
    assert b['point_diff_difference']==0


def test_later_games_see_past_only():
    feat,hist=build_features(sample());w2=feat[feat.week==2].iloc[0]
    assert w2['games_played_difference']==0
    assert w2['points_for_difference']!=0
    assert feat[feat.week==3].shape[0]==1


def test_ties_are_not_binary_training_targets():
    d=sample();d.loc[d.game_id=='2023_02_A_C','home_score']=31
    feat,_=build_features(d)
    assert pd.isna(feat.loc[feat.game_id=='2023_02_A_C','outcome'].iloc[0])


def test_team_canonicalization():
    assert clean(pd.DataFrame([{'game_id':'2024_01_X_OAK','season':2024,'game_type':'REG','week':1,'away_team':'SD','home_team':'OAK','away_score':7,'home_score':9}])).iloc[0].home_team=='LV'
