import time
from functools import wraps
from backend.observability.metrics import metrics

def timed(metric_name: str):
    """Decorator that records execution time."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.monotonic() - start
                metrics.observe(f"{metric_name}_duration_seconds", elapsed)
        return wrapper
    return decorator