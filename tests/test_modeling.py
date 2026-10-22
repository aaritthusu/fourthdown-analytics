from fastapi.testclient import TestClient
from backend.main import app
from backend.modeling import ARTIFACT,REPORT
from backend.data import load_data
from backend.features import build_features,FEATURE_NAMES


def test_saved_training_artifacts_are_real():
    assert ARTIFACT.exists() and REPORT.exists()
    games,_=load_data()
    features,_=build_features(games)
    assert len(features.dropna(subset=['outcome']))>=100
    assert not features[FEATURE_NAMES].isna().any().any()


def test_prediction_probability_integrity_and_future_only():
    with TestClient(app) as client:
        o=client.get('/api/overview').json()
        p=client.get('/api/predictions')
        assert p.status_code==200
        games=p.json()['games']
        assert games
        for game in games:
            pred=game['prediction']
            assert pred is not None
            assert 0<=pred['home_win_probability']<=1
            assert 0<=pred['away_win_probability']<=1
            assert abs(pred['home_win_probability']+pred['away_win_probability']-1)<.00011
            assert pred['partial_coverage']==o['partial_coverage']
        r=client.get('/api/predict',params={'home':'KC','away':'BUF','season':o['season']-1,'week':1})
        assert r.status_code==422  # No after-the-fact historical inference


def test_backtest_provenance_and_pagination():
    with TestClient(app) as client:
        r=client.get('/api/performance');assert r.status_code==200
        report=r.json()
        assert report['test']['count']==report['test_games']
        assert report['validation_season']<report['test_season']
        assert report['test']['confusion']
        r=client.get('/api/games',params={'season':report['test_season'],'result':'final','limit':5})
        assert r.status_code==200
        d=r.json();assert len(d['games'])<=5
        assert d['count']>=5
