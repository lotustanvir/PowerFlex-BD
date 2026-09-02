"""Weather Provider Abstraction for PowerFlex BD v3.

Provides a unified interface for weather data from multiple providers.
Currently integrates Open-Meteo as the primary provider.

Only use variables actually provided by the weather API.
NEVER fabricate weather data.
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger("powerflex.weather")

WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", "1800"))  # 30 minutes


@dataclass
class WeatherDataPoint:
    """Single weather data point for a location."""
    latitude: float
    longitude: float
    timestamp: str
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_degree: Optional[float] = None
    cloud_cover_percent: Optional[float] = None
    precipitation_mm: Optional[float] = None
    pressure_hpa: Optional[float] = None
    solar_radiation_wm2: Optional[float] = None
    direct_normal_irradiance_wm2: Optional[float] = None
    diffuse_radiation_wm2: Optional[float] = None
    source: str = "unknown"
    quality: str = "GOOD"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
            "wind_speed_kmh": self.wind_speed_kmh,
            "wind_direction_degree": self.wind_direction_degree,
            "cloud_cover_percent": self.cloud_cover_percent,
            "precipitation_mm": self.precipitation_mm,
            "pressure_hpa": self.pressure_hpa,
            "solar_radiation_wm2": self.solar_radiation_wm2,
            "direct_normal_irradiance_wm2": self.direct_normal_irradiance_wm2,
            "diffuse_radiation_wm2": self.diffuse_radiation_wm2,
            "source": self.source,
            "quality": self.quality,
        }


@dataclass
class WeatherForecast:
    """Weather forecast for a location over multiple hours."""
    latitude: float
    longitude: float
    timezone: str
    hourly: List[WeatherDataPoint] = field(default_factory=list)
    source: str = "unknown"
    retrieved_at: str = ""
    provider: str = "unknown"
    classification: str = "LIVE_FEED"
    quality: str = "GOOD"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "hourly": [h.to_dict() for h in self.hourly],
            "source": self.source,
            "retrieved_at": self.retrieved_at,
            "provider": self.provider,
            "classification": self.classification,
            "quality": self.quality,
            "hour_count": len(self.hourly),
        }


class WeatherProvider(ABC):
    """Abstract base class for weather data providers."""

    @abstractmethod
    def get_current(
        self, latitude: float, longitude: float
    ) -> Optional[WeatherDataPoint]:
        """Get current weather for a location."""
        ...

    @abstractmethod
    def get_forecast(
        self, latitude: float, longitude: float, hours: int = 24
    ) -> Optional[WeatherForecast]:
        """Get weather forecast for a location."""
        ...

    @abstractmethod
    def get_historical(
        self, latitude: float, longitude: float,
        start_date: str, end_date: str
    ) -> List[WeatherDataPoint]:
        """Get historical weather data."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        ...


class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo weather data provider.

    Free tier: 10,000 requests/day.
    Variables: temperature, humidity, wind, cloud cover, irradiance.

    Includes retry logic, rate-limit handling, and circuit breaker.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    MAX_RETRIES = 2
    RETRY_BACKOFF = [1.0, 3.0]  # seconds

    def __init__(self):
        self._available = True
        self._last_check = 0
        self._check_interval = 300  # 5 minutes
        self._consecutive_failures = 0
        self._circuit_open_until = 0  # timestamp when circuit closes
        self._last_rate_limit = 0  # timestamp of last 429

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open (too many failures)."""
        if self._consecutive_failures >= 5:
            if time.time() < self._circuit_open_until:
                return True
            # Reset after cooldown
            self._consecutive_failures = 0
        return False

    def _record_success(self):
        """Record a successful request."""
        self._consecutive_failures = 0
        self._available = True

    def _record_failure(self, status_code: int = 0):
        """Record a failed request."""
        if status_code == 429:
            self._last_rate_limit = time.time()
            # On rate limit, back off significantly
            self._consecutive_failures = max(self._consecutive_failures + 3, 5)
            self._circuit_open_until = time.time() + 300  # 5 min cooldown
            logger.warning("Open-Meteo rate limited (429). Circuit open for 5 min.")
        else:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                self._circuit_open_until = time.time() + 60
                logger.warning("Open-Meteo circuit breaker open after %d failures.", self._consecutive_failures)

    def _check_availability(self) -> bool:
        """Periodically check if Open-Meteo is accessible."""
        now = time.time()
        if now - self._last_check < self._check_interval:
            return self._available and not self._is_circuit_open()

        self._last_check = now
        try:
            resp = requests.get(
                self.BASE_URL,
                params={
                    "latitude": 23.8103,
                    "longitude": 90.4125,
                    "current_weather": "true",
                    "forecast_days": 1,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                self._record_success()
            elif resp.status_code == 429:
                self._record_failure(429)
            else:
                self._available = False
        except Exception:
            self._available = False

        return self._available and not self._is_circuit_open()

    def is_available(self) -> bool:
        return self._check_availability()

    def _request_with_retry(self, params: dict, timeout: int = 15) -> Optional[requests.Response]:
        """Make a request with retry logic and rate-limit handling."""
        for attempt in range(self.MAX_RETRIES + 1):
            if self._is_circuit_open():
                logger.warning("Open-Meteo circuit breaker open, skipping request.")
                return None

            try:
                resp = requests.get(self.BASE_URL, params=params, timeout=timeout)

                if resp.status_code == 200:
                    self._record_success()
                    return resp
                elif resp.status_code == 429:
                    self._record_failure(429)
                    if attempt < self.MAX_RETRIES:
                        wait = self.RETRY_BACKOFF[min(attempt, len(self.RETRY_BACKOFF) - 1)]
                        logger.info("Rate limited, waiting %.1fs before retry.", wait)
                        time.sleep(wait)
                        continue
                    return resp
                else:
                    logger.warning("Open-Meteo returned %d", resp.status_code)
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.RETRY_BACKOFF[min(attempt, len(self.RETRY_BACKOFF) - 1)])
                        continue
                    return resp

            except requests.exceptions.Timeout:
                self._record_failure()
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_BACKOFF[min(attempt, len(self.RETRY_BACKOFF) - 1)])
                    continue
                return None
            except Exception as e:
                self._record_failure()
                logger.warning("Open-Meteo request failed: %s", e)
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_BACKOFF[min(attempt, len(self.RETRY_BACKOFF) - 1)])
                    continue
                return None

        return None

    def get_current(
        self, latitude: float, longitude: float
    ) -> Optional[WeatherDataPoint]:
        if not self.is_available():
            logger.warning("Open-Meteo not available")
            return None

        try:
            resp = self._request_with_retry(
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current_weather": "true",
                    "hourly": (
                        "temperature_2m,relative_humidity_2m,"
                        "cloud_cover,wind_speed_10m,wind_direction_10m,"
                        "shortwave_radiation"
                    ),
                    "forecast_days": 1,
                },
                timeout=15,
            )

            if resp is None or resp.status_code != 200:
                return None

            data = resp.json()
            current = data.get("current_weather", {})
            hourly = data.get("hourly", {})

            now = datetime.now(timezone.utc)
            hour_idx = now.hour

            temperature = hourly.get("temperature_2m", [None])[hour_idx]
            humidity = hourly.get("relative_humidity_2m", [None])[hour_idx]
            cloud_cover = hourly.get("cloud_cover", [None])[hour_idx]
            wind_speed = current.get("windspeed", hourly.get("wind_speed_10m", [None])[hour_idx])
            wind_dir = current.get("winddirection", hourly.get("wind_direction_10m", [None])[hour_idx])
            radiation = hourly.get("shortwave_radiation", [None])[hour_idx]

            return WeatherDataPoint(
                latitude=latitude,
                longitude=longitude,
                timestamp=now.isoformat(),
                temperature_c=temperature,
                humidity_percent=humidity,
                wind_speed_kmh=wind_speed,
                wind_direction_degree=wind_dir,
                cloud_cover_percent=cloud_cover,
                solar_radiation_wm2=radiation,
                source="open_meteo",
                quality="GOOD" if any(v is not None for v in [temperature, humidity, wind_speed]) else "PARTIAL",
            )

        except Exception as e:
            logger.error("Open-Meteo current weather failed: %s", e)
            return None

    def get_forecast(
        self, latitude: float, longitude: float, hours: int = 24
    ) -> Optional[WeatherForecast]:
        if not self.is_available():
            return None

        try:
            forecast_days = max(1, (hours + 23) // 24)
            resp = requests.get(
                self.BASE_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": (
                        "temperature_2m,relative_humidity_2m,"
                        "precipitation,cloud_cover,wind_speed_10m,"
                        "wind_direction_10m,shortwave_radiation,"
                        "direct_normal_irradiance,diffuse_radiation"
                    ),
                    "forecast_days": min(forecast_days, 16),
                },
                timeout=15,
            )

            if resp.status_code != 200:
                logger.warning("Open-Meteo forecast returned %d", resp.status_code)
                return None

            data = resp.json()
            hourly_data = data.get("hourly", {})
            times = hourly_data.get("time", [])

            now = datetime.now(timezone.utc)
            start_idx = 0
            for i, t in enumerate(times):
                try:
                    dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
                    if dt >= now.replace(minute=0, second=0, microsecond=0):
                        start_idx = i
                        break
                except ValueError:
                    continue

            end_idx = min(start_idx + hours, len(times))
            hourly_points = []

            for i in range(start_idx, end_idx):
                point = WeatherDataPoint(
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=times[i],
                    temperature_c=hourly_data.get("temperature_2m", [None])[i],
                    humidity_percent=hourly_data.get("relative_humidity_2m", [None])[i],
                    wind_speed_kmh=hourly_data.get("wind_speed_10m", [None])[i],
                    wind_direction_degree=hourly_data.get("wind_direction_10m", [None])[i],
                    cloud_cover_percent=hourly_data.get("cloud_cover", [None])[i],
                    precipitation_mm=hourly_data.get("precipitation", [None])[i],
                    solar_radiation_wm2=hourly_data.get("shortwave_radiation", [None])[i],
                    direct_normal_irradiance_wm2=hourly_data.get("direct_normal_irradiance", [None])[i],
                    diffuse_radiation_wm2=hourly_data.get("diffuse_radiation", [None])[i],
                    source="open_meteo",
                )
                hourly_points.append(point)

            return WeatherForecast(
                latitude=latitude,
                longitude=longitude,
                timezone=data.get("timezone", "Asia/Dhaka"),
                hourly=hourly_points,
                source="open_meteo",
                retrieved_at=now.isoformat(),
                provider="open-meteo",
                classification="LIVE_FEED",
                quality="GOOD" if hourly_points else "UNAVAILABLE",
            )

        except Exception as e:
            logger.error("Open-Meteo forecast failed: %s", e)
            return None

    def get_historical(
        self, latitude: float, longitude: float,
        start_date: str, end_date: str
    ) -> List[WeatherDataPoint]:
        """Get historical weather from Open-Meteo archive API."""
        try:
            resp = requests.get(
                "https://archive-api.open-meteo.com/v1/archive",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": start_date,
                    "end_date": end_date,
                    "daily": (
                        "temperature_2m_max,temperature_2m_min,"
                        "precipitation_sum,wind_speed_10m_max"
                    ),
                },
                timeout=15,
            )

            if resp.status_code != 200:
                return []

            data = resp.json()
            daily = data.get("daily", {})
            dates = daily.get("time", [])

            points = []
            for i, date in enumerate(dates):
                points.append(WeatherDataPoint(
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=f"{date}T12:00:00+06:00",
                    temperature_c=(
                        (daily.get("temperature_2m_max", [None])[i] or 0) +
                        (daily.get("temperature_2m_min", [None])[i] or 0)
                    ) / 2 if daily.get("temperature_2m_max", [None])[i] is not None else None,
                    precipitation_mm=daily.get("precipitation_sum", [None])[i],
                    wind_speed_kmh=daily.get("wind_speed_10m_max", [None])[i],
                    source="open_meteo_archive",
                ))

            return points

        except Exception as e:
            logger.error("Open-Meteo historical failed: %s", e)
            return []


# =========================================================
# WEATHER CACHE
# =========================================================

class WeatherCache:
    """In-memory cache for weather data with stale fallback."""

    def __init__(self, ttl: int = WEATHER_CACHE_TTL):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._ttl = ttl

    def _key(self, lat: float, lon: float, data_type: str) -> str:
        return f"weather:{lat:.4f}:{lon:.4f}:{data_type}"

    def get(self, lat: float, lon: float, data_type: str) -> Optional[Any]:
        """Get cached data if fresh."""
        key = self._key(lat, lon, data_type)
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
        return None

    def get_stale(self, lat: float, lon: float, data_type: str) -> Optional[Any]:
        """Get cached data even if stale (for fallback)."""
        key = self._key(lat, lon, data_type)
        if key in self._cache:
            _, data = self._cache[key]
            return data
        return None

    def get_age(self, lat: float, lon: float, data_type: str) -> Optional[float]:
        """Get age of cached data in seconds."""
        key = self._key(lat, lon, data_type)
        if key in self._cache:
            timestamp, _ = self._cache[key]
            return time.time() - timestamp
        return None

    def set(self, lat: float, lon: float, data_type: str, data: Any) -> None:
        key = self._key(lat, lon, data_type)
        self._cache[key] = (time.time(), data)

    def clear(self) -> None:
        self._cache.clear()


# =========================================================
# SINGLETON INSTANCES
# =========================================================

_provider: Optional[OpenMeteoProvider] = None
_cache: Optional[WeatherCache] = None


def get_weather_provider() -> OpenMeteoProvider:
    global _provider
    if _provider is None:
        _provider = OpenMeteoProvider()
    return _provider


def get_weather_cache() -> WeatherCache:
    global _cache
    if _cache is None:
        _cache = WeatherCache()
    return _cache
