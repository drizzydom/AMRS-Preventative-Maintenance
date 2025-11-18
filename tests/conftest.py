import pytest

from tests.rbac_test_utils import create_seeded_app, teardown_app


@pytest.fixture()
def app():
    app, _ = create_seeded_app()
    yield app
    teardown_app(app)


@pytest.fixture()
def client(app):
    return app.test_client()
