"""Regression tests for production-hardening security primitives."""
from backend.core.security import create_access_token, decode_token
from backend.services.playwright_engine import AccessibilityScanner
from backend.services.url_safety import _is_forbidden_ip


def test_private_and_loopback_ips_are_blocked():
    for value in ('127.0.0.1', '10.0.0.1', '172.16.0.1', '192.168.1.1', '169.254.169.254', '::1', 'fc00::1', 'fe80::1'):
        assert _is_forbidden_ip(value), value


def test_public_ips_are_not_classified_private():
    assert not _is_forbidden_ip('1.1.1.1')
    assert not _is_forbidden_ip('8.8.8.8')


def test_access_token_uses_user_id_and_expected_claims():
    token = create_access_token(user_id='user-123')
    payload = decode_token(token, 'access')
    assert payload['sub'] == 'user-123'
    assert payload['type'] == 'access'
    assert payload['jti']
    assert payload['iat']
    assert payload['iss']
    assert payload['aud']


def test_health_score_is_not_fabricated_when_no_rules_run():
    assert AccessibilityScanner.calculate_axe_score({'violations': [], 'passes': []}) == 0


def test_health_score_penalizes_more_severe_failures():
    mild = {
        'violations': [{'impact': 'minor', 'nodes': [{}]}],
        'passes': [{}],
    }
    severe = {
        'violations': [{'impact': 'critical', 'nodes': [{}, {}]}],
        'passes': [{}],
    }
    assert AccessibilityScanner.calculate_axe_score(severe) < AccessibilityScanner.calculate_axe_score(mild)
