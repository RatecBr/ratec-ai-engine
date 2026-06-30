from datetime import datetime, timezone

# We'll need a way to track boot time
_BOOT_TIME = datetime.now(timezone.utc)

def get_platform_health() -> dict:
    """
    Retorna a saude global da plataforma
    """
    uptime = int((datetime.now(timezone.utc) - _BOOT_TIME).total_seconds())
    
    return {
        "status": "ok",
        "version": "1.1.0-alpha", # TODO get from config
        "uptime_seconds": uptime,
        "availability": "online"
    }
