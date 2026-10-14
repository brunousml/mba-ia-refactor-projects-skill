def completion_rate(done, total):
    """Percentual concluído com 2 casas; 0 quando não há tasks."""
    return round((done / total) * 100, 2) if total > 0 else 0
