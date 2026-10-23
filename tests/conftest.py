from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def isolate_activities():
    original = deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(original)


@pytest.fixture
def client(isolate_activities):
    with TestClient(app) as test_client:
        yield test_client