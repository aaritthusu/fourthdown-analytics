"""Trend counts and evidence must agree with real completed games."""
import pandas as pd
from fastapi.testclient import TestClient
from backend.trends import trends
from backend.data import clean
from backend.main import app


def sample():
    records=[]
    for week,(h,a,hs,aw) in enumerate([
        ('KC','BUF',30,17),('BUF','KC',14,27),('KC','BUF',28,20),
        ('KC','LV',10,14),('BUF','KC',31,22),('KC','BUF',35,28),
        ('KC','BUF',None,None),
    ],start=1):
        records.append({'game_id':f'2024_{week:02}_{a}_{h}', 'season':2024,'game_type':'REG','week':week,
                        'gameday':f'2024-09-{week+2:02}', 'home_team':h,'away_team':a,'home_score':hs,'away_score':aw})
    return clean(pd.DataFrame(records))


def test_specific_home_versus_opponent_streak_is_scoped_correctly():
    x=trends(sample(),'KC','BUF','home',5)
    assert x['sample_games']==3
    assert x['available_games']==3
    card=next(c for c in x['cards'] if c['id']=='h2h-home')
    assert (card['hits'],card['sample'],card['current_streak']) == (3,3,3)
    assert len(card['game_ids'])==3
    assert all(g['venue']=='home' and g['opponent']=='BUF' for g in card['games'])
    assert '2024_07' not in ''.join(str(g['id']) for g in x['recent_games'])


def test_multiple_non_win_trend_categories_have_verifiable_counts():
    x=trends(sample(),'KC',None, 'all', 5, partial=True)
    assert x['partial_coverage']
    assert {c['category'] for c in x['cards']} >= {'Offense','Defense','Results','Game flow'}
    for c in x['cards']:
        assert len(c['game_ids'])==c['hits']
        assert c['sample']>=c['hits']>=0
        assert c['rate']==round(c['hits']/c['sample'],3)
    assert all(g['id']!='2024_07_BUF_KC' for g in x['recent_games'])


def test_small_samples_never_present_streak_cards():
    x=trends(sample(),'KC','LV','home',5)
    assert x['sample_games']==1
    assert x['cards']==[]


def test_api_validation_and_real_data_response():
    with TestClient(app) as client:
        r=client.get('/api/trends',params={'team':'KC','last':5})
        assert r.status_code==200
        data=r.json()
        assert data['team']=='KC' and isinstance(data['cards'],list)
        assert client.get('/api/trends',params={'team':'KC','venue':'moon'}).status_code==422
        assert client.get('/api/trends',params={'team':'KC','opponent':'KC'}).status_code==422
