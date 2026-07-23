from app.core.status import status_by_ratio


def test_up_metric_ok():
    ratio, status = status_by_ratio(120, 100, "up")
    assert ratio >= 1
    assert "Выполнено" in status


def test_down_metric_exceeded():
    ratio, status = status_by_ratio(178, 21, "down", 1.3)
    assert ratio < 1
    assert "Превышение" in status or "Риск" in status
