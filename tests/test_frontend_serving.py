"""The compiled frontend must not intercept HTTP method errors from API routes."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('compiled', [False, True])
def test_frontend_preserves_api_methods(tmp_path, compiled):
    dist = tmp_path / 'dist'
    if compiled:
        (dist / 'assets').mkdir(parents=True)
        (dist / 'index.html').write_text('<html>ORQENTIVA test</html>', encoding='utf-8')
        (dist / 'favicon.svg').write_text('<svg/>', encoding='utf-8')
        # Even an accidental file named like an API endpoint cannot shadow it.
        (dist / 'leads').write_text('not an API response', encoding='utf-8')
    env = dict(os.environ, FRONTEND_DIST=str(dist))
    code = '''
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    response = client.get('/leads')
    assert response.status_code == 405, response.text
    assert 'POST' in response.headers['allow']
    assert client.post('/leads', json={}).status_code == 422
    assert client.post('/health').status_code == 405
    assert client.get('/health').status_code == 200
    assert client.get('/missing-file').status_code == 404
'''
    if compiled:
        code += "    assert client.get('/').status_code == 200\n    assert client.get('/favicon.svg').text == '<svg/>'\n"
    result = subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[1],
                            env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
