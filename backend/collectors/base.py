from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

@dataclass
class CollectorResult:
    source: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latency_ms: Optional[float] = None
    record_count: int = 0

class BaseCollector(ABC):
    def __init__(self, name: str, timeout: int = 30):
        self.name = name
        self.timeout = timeout
        self.logger = logging.getLogger(f"powerflex.collector.{name}")

    @abstractmethod
    def collect(self) -> CollectorResult:
        pass

    def validate(self, data: Dict[str, Any]) -> bool:
        return data is not None and len(data) > 0
