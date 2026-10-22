from fastapi.testclient import TestClient
from backend.main import app

def test_health_route():
    r=TestClient(app).get('/api/health')
    assert r.status_code==200
    assert 'model_loaded' in r.json()

def test_input_validation():
    with TestClient(app) as c:
        r=c.get('/api/predict?home=KC&away=KC&week=19')
        assert r.status_code==422
