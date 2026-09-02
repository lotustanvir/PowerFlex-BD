import time

from backend.collectors.base import BaseCollector, CollectorResult
from backend.waste_calculator import calculate_all_cities, map_waste_to_zones


class WasteCollector(BaseCollector):
    def __init__(self, timeout: int = 30):
        super().__init__(name="waste_calculator", timeout=timeout)

    def collect(self) -> CollectorResult:
        start = time.monotonic()
        try:
            city_results = calculate_all_cities()
            zone_results = map_waste_to_zones(
                city_results.get("cities", {})
            )
            latency_ms = (time.monotonic() - start) * 1000

            national = city_results.get("national", {})
            cities = city_results.get("cities", {})

            data = {
                "cities": cities,
                "zones": zone_results,
                "national": national,
                "conversion_factors": city_results.get(
                    "conversion_factors", {}
                ),
            }

            return CollectorResult(
                source="WASTE_CALCULATOR",
                success=True,
                data=data,
                latency_ms=round(latency_ms, 2),
                record_count=len(cities),
            )

        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return CollectorResult(
                source="WASTE_CALCULATOR",
                success=False,
                error=str(exc),
                latency_ms=round(latency_ms, 2),
            )
