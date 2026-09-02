import time
from typing import Optional

from backend.collectors.base import BaseCollector, CollectorResult
from backend.grid import fetch_pgcb_grid_data, detect_stale_data, PGCB_STALE_THRESHOLD_HOURS


class GridCollector(BaseCollector):
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        super().__init__(name="pgcb_grid", timeout=timeout)
        self.max_retries = max_retries

    def collect(self) -> CollectorResult:
        last_error: Optional[str] = None
        for attempt in range(self.max_retries):
            start = time.monotonic()
            try:
                result = fetch_pgcb_grid_data()
                latency_ms = (time.monotonic() - start) * 1000

                if not result.get("connected"):
                    last_error = result.get("message", "Unknown error")
                    self.logger.warning(
                        "Attempt %d/%d failed: %s",
                        attempt + 1,
                        self.max_retries,
                        last_error,
                    )
                    time.sleep(2 ** attempt)
                    continue

                data = result.get("data", {})
                timestamp = data.get("timestamp", "")
                stale = detect_stale_data(timestamp) if timestamp else True

                record_count = 0
                if data:
                    record_count = sum(
                        1 for v in data.values()
                        if v is not None and v != ""
                    )

                if stale:
                    self.logger.warning(
                        "PGCB data is stale (>%dh old): %s",
                        PGCB_STALE_THRESHOLD_HOURS,
                        timestamp,
                    )

                return CollectorResult(
                    source="PGCB_GRID",
                    success=True,
                    data=data,
                    latency_ms=round(latency_ms, 2),
                    record_count=record_count,
                )

            except Exception as exc:
                latency_ms = (time.monotonic() - start) * 1000
                last_error = str(exc)
                self.logger.warning(
                    "Attempt %d/%d exception: %s",
                    attempt + 1,
                    self.max_retries,
                    last_error,
                )
                time.sleep(2 ** attempt)

        return CollectorResult(
            source="PGCB_GRID",
            success=False,
            error=f"All {self.max_retries} retries exhausted: {last_error}",
        )
