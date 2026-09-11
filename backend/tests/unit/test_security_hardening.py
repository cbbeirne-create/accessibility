import asyncio

import pytest

from backend.core.security import generate_refresh_token, hash_refresh_token
from backend.services.playwright_engine import AccessibilityScanner
from backend.services.url_security import UnsafeScanTarget, validate_scan_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]",
        "ftp://example.com/file",
        "http://example.com:22",
    ],
)
def test_private_and_unsafe_targets_are_rejected(url):
    with pytest.raises(UnsafeScanTarget):
        asyncio.run(validate_scan_url(url))


def test_refresh_tokens_are_random_and_only_hashes_need_persistence():
    first = generate_refresh_token()
    second = generate_refresh_token()
    assert first != second
    assert len(first) >= 48
    assert hash_refresh_token(first) != first
    assert hash_refresh_token(first) == hash_refresh_token(first)


def test_health_score_is_bounded_and_not_magic_floor():
    perfect = {"violations": [], "passes": [{"nodes": [{}, {}]}]}
    poor = {
        "violations": [{"impact": "critical", "nodes": [{}, {}, {}]}],
        "passes": [{"nodes": [{}]}],
    }
    assert AccessibilityScanner.calculate_axe_score(perfect) == 100
    assert 0 <= AccessibilityScanner.calculate_axe_score(poor) < 50
