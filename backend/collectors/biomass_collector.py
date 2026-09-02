import time

from backend.collectors.base import BaseCollector, CollectorResult
from backend.biomass_calculator import calculate_all_divisions


class BiomassCollector(BaseCollector):
    def __init__(self, use_fallback: bool = False, timeout: int = 30):
        super().__init__(name="biomass_calculator", timeout=timeout)
        self.use_fallback = use_fallback

    def collect(self) -> CollectorResult:
        start = time.monotonic()
        try:
            result = calculate_all_divisions(
                use_fallback=self.use_fallback
            )
            latency_ms = (time.monotonic() - start) * 1000

            national = result.get("national", {})
            divisions = result.get("divisions", {})

            return CollectorResult(
                source="BIOMASS_CALCULATOR",
                success=True,
                data=result,
                latency_ms=round(latency_ms, 2),
                record_count=len(divisions),
            )

        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return CollectorResult(
                source="BIOMASS_CALCULATOR",
                success=False,
                error=str(exc),
                latency_ms=round(latency_ms, 2),
            )
