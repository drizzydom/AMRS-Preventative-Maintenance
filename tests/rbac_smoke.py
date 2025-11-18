"""Simple RBAC smoke test runner.

This script spins up the same in-memory app the pytest fixtures use and
executes a few high-level flows that mimic how real roles exercise the API.
Run it with `python -m tests.rbac_smoke` from the repo root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from tests.rbac_test_utils import create_seeded_app, teardown_app


@dataclass
class ApiStep:
    description: str
    method: str
    path: str
    expect_status: int
    validate: Callable[[Dict], None] | None = None


@dataclass
class Scenario:
    name: str
    username: str
    password: str
    steps: List[ApiStep] = field(default_factory=list)


def login(client, username: str, password: str):
    response = client.post('/api/v1/auth/login', json={'username': username, 'password': password})
    assert response.status_code == 200, response.get_json()


def logout(client):
    client.post('/api/v1/auth/logout')


def run_scenario(client, scenario: Scenario) -> List[str]:
    notes = [f"Scenario: {scenario.name}"]
    login(client, scenario.username, scenario.password)

    for step in scenario.steps:
        response = client.open(step.path, method=step.method)
        status = response.status_code
        ok = status == step.expect_status
        summary = f"  {step.description}: {status} (expected {step.expect_status})"
        notes.append(summary)
        if not ok:
            notes.append(f"    FAILED payload: {response.get_data(as_text=True)}")
            break
        if step.validate:
            payload = response.get_json()
            step.validate(payload)

    logout(client)
    return notes


def validate_machine_scope(expected_names: List[str]) -> Callable[[Dict], None]:
    def _validator(payload: Dict):
        names = sorted(machine['site_name'] for machine in payload['data'])
        assert names == sorted(expected_names), f"Expected machine sites {expected_names}, got {names}"
    return _validator


def validate_audit_scope(expected_count: int) -> Callable[[Dict], None]:
    def _validator(payload: Dict):
        assert len(payload['data']) == expected_count, f"Expected {expected_count} audits"
    return _validator


def validate_sites(expected_count: int) -> Callable[[Dict], None]:
    def _validator(payload: Dict):
        assert len(payload['data']) == expected_count, f"Expected {expected_count} sites"
    return _validator


def build_scenarios() -> List[Scenario]:
    return [
        Scenario(
            name='Admin full access',
            username='admin',
            password='password',
            steps=[
                ApiStep('machines listing', 'GET', '/api/v1/machines', 200, validate_machine_scope(['Alpha Plant', 'Beta Plant'])),
                ApiStep('sites listing', 'GET', '/api/v1/sites', 200, validate_sites(2)),
                ApiStep('audits listing', 'GET', '/api/v1/audits', 200, validate_audit_scope(2)),
            ],
        ),
        Scenario(
            name='Limited technician scoped to Alpha',
            username='limited',
            password='password',
            steps=[
                ApiStep('machines limited listing', 'GET', '/api/v1/machines', 200, validate_machine_scope(['Alpha Plant'])),
                ApiStep('sites forbidden', 'GET', '/api/v1/sites', 403),
                ApiStep('audits scoped listing', 'GET', '/api/v1/audits', 200, validate_audit_scope(1)),
            ],
        ),
        Scenario(
            name='Basic viewer minimal permissions',
            username='basic',
            password='password',
            steps=[
                ApiStep('machines readonly listing', 'GET', '/api/v1/machines', 200, validate_machine_scope(['Alpha Plant'])),
                ApiStep('audits blocked', 'GET', '/api/v1/audits', 403),
            ],
        ),
    ]


def main():
    app, _ = create_seeded_app()
    notes: List[str] = []
    success = True

    with app.app_context():
        client = app.test_client()
        for scenario in build_scenarios():
            try:
                scenario_notes = run_scenario(client, scenario)
                notes.extend(scenario_notes)
            except AssertionError as exc:
                notes.append(f"Scenario '{scenario.name}' FAILED: {exc}")
                success = False
                break

    teardown_app(app)

    print('\n'.join(notes))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
