"""Deployment config smoke tests (without reaching external cloud services)."""
from pathlib import Path

from fastapi.testclient import TestClient
from backend.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_cors_local_development():
    response = TestClient(app).options(
        '/api/overview',
        headers={'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'GET'},
    )
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:3000'


def test_render_deployment_files_exist():
    blueprint = (ROOT / 'render.yaml').read_text()
    assert 'healthCheckPath: /api/health' in blueprint
    assert 'backend.main:app' in blueprint
    assert (ROOT / '.python-version').read_text().strip().startswith('3.13')


def test_public_docs_explain_env_vars():
    docs = (ROOT / 'PUBLIC_DEPLOYMENT.md').read_text()
    assert 'NEXT_PUBLIC_API_BASE_URL' in docs
    assert 'FRONTEND_ORIGINS' in docs
    assert 'perfect' in docs.lower()
