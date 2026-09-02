import concurrent.futures
import time
from typing import Any, Dict, Optional

import requests

from backend.collectors.base import BaseCollector, CollectorResult


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

SOLAR_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "shortwave_radiation",
]

WIND_PARAMS = [
    "wind_speed_10m",
    "wind_speed_80m",
    "wind_speed_100m",
    "wind_speed_120m",
    "wind_direction_10m",
    "wind_direction_100m",
    "wind_direction_120m",
    "wind_gusts_10m",
    "temperature_2m",
    "pressure_msl",
]

LOCATIONS: Dict[str, tuple] = {
    "Dhaka": (23.8103, 90.4125),
    "Chittagong": (22.3569, 91.7832),
    "Khulna": (22.8456, 89.5403),
    "Rajshahi": (24.3745, 88.6042),
    "Comilla": (23.4607, 91.1809),
    "Mymensingh": (24.7471, 90.4203),
    "Sylhet": (24.8949, 91.8687),
    "Barishal": (22.7010, 90.3535),
    "Rangpur": (25.7439, 89.2752),
}


def _fetch_zone_weather(
    zone: str,
    latitude: float,
    longitude: float,
    params_list: list,
    forecast_hours: int,
    timeout: int,
) -> list:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(params_list),
        "forecast_hours": forecast_hours,
        "timezone": "Asia/Dhaka",
        "wind_speed_unit": "kmh",
    }
    response = requests.get(
        OPEN_METEO_URL, params=params, timeout=timeout
    )
    response.raise_for_status()
    data = response.json()
    hourly = data["hourly"]
    rows: list = []
    for i in range(len(hourly["time"])):
        row: Dict[str, Any] = {
            "zone": zone,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": hourly["time"][i],
        }
        for key in params_list:
            if key in hourly:
                row[key] = hourly[key][i]
        rows.append(row)
    return rows


class WeatherCollector(BaseCollector):
    def __init__(
        self,
        timeout: int = 30,
        forecast_hours: int = 24,
        max_workers: int = 5,
    ):
        super().__init__(name="open_meteo_weather", timeout=timeout)
        self.forecast_hours = forecast_hours
        self.max_workers = max_workers

    def collect(self) -> CollectorResult:
        start = time.monotonic()
        try:
            all_rows: list = []
            failed_zones: list = []

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as pool:
                futures: Dict[concurrent.futures.Future, str] = {}
                for zone, (lat, lon) in LOCATIONS.items():
                    future = pool.submit(
                        _fetch_zone_weather,
                        zone,
                        lat,
                        lon,
                        SOLAR_PARAMS + WIND_PARAMS,
                        self.forecast_hours,
                        self.timeout,
                    )
                    futures[future] = zone

                for future in concurrent.futures.as_completed(futures):
                    zone = futures[future]
                    try:
                        rows = future.result()
                        all_rows.extend(rows)
                    except Exception as exc:
                        self.logger.warning(
                            "Zone %s failed: %s", zone, exc
                        )
                        failed_zones.append(zone)

            latency_ms = (time.monotonic() - start) * 1000

            if not all_rows:
                return CollectorResult(
                    source="OPEN_METEO",
                    success=False,
                    error="All weather zones failed",
                    latency_ms=round(latency_ms, 2),
                )

            zones_succeeded = len(LOCATIONS) - len(failed_zones)
            data = {
                "hourly_data": all_rows,
                "zones_succeeded": zones_succeeded,
                "zones_failed": len(failed_zones),
                "failed_zones": failed_zones,
                "total_records": len(all_rows),
                "forecast_hours": self.forecast_hours,
            }

            return CollectorResult(
                source="OPEN_METEO",
                success=True,
                data=data,
                latency_ms=round(latency_ms, 2),
                record_count=len(all_rows),
            )

        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return CollectorResult(
                source="OPEN_METEO",
                success=False,
                error=str(exc),
                latency_ms=round(latency_ms, 2),
            )
