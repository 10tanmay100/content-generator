"""Shared pytest fixtures."""
import os
import sys
from pathlib import Path

os.environ.setdefault("API_AUTH_TOKEN", "test-token")
os.environ.setdefault("ENVIRONMENT", "development")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test-token"}