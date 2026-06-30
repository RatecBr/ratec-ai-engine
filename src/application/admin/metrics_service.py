def get_system_metrics() -> dict:
    """
    Retorna metricas de performance e throughput
    """
    return {
        "avg_execution_ms": 1500,
        "throughput_per_hour": 120,
        "total_jobs": 45,
        "benchmarks": {
            "txt2img_avg_ms": 2200
        }
    }
