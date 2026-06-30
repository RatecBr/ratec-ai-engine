from datetime import datetime, timezone

def get_platform_logs(log_type: str = "all") -> list:
    """
    Retorna ultimos logs da plataforma
    """
    now = datetime.now(timezone.utc).isoformat()
    # Mock data for demonstration
    return [
        {"timestamp": now, "level": "INFO", "message": "RATEC AI ENGINE initialized successfully."},
        {"timestamp": now, "level": "INFO", "message": f"Filter applied: {log_type}"}
    ]
