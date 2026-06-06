from src.app import health_check


def test_health_check():
    result = health_check()
    assert result["project"] == "pi-gateway-watch"
    assert result["status"] == "starter_ready"
    assert result["safe_to_publish"] is True
