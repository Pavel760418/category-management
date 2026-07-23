def status_by_ratio(actual, target, direction="up", risk_multiplier=1.0):
    if actual is None or target in (None, 0):
        return None, "Недоступно"
    if direction == "up":
        ratio = actual / target if target else None
        if ratio is None:
            return None, "Недоступно"
        if ratio >= 1:
            return ratio, "🟢 Выполнено"
        if ratio >= 0.85:
            return ratio, "🟡 Риск"
        return ratio, "🔴 Не выполнено"
    ratio = 1 if actual <= target else (target / actual if actual else None)
    if actual <= target:
        return ratio, "🟢 Выполнено"
    if actual <= target * risk_multiplier:
        return ratio, "🟡 Риск"
    return ratio, "🔴 Превышение"
