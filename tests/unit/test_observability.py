import json
import logging
import time
from backend.observability.logging import StructuredFormatter, setup_structured_logging
from backend.observability.metrics import MetricsCollector, metrics
from backend.observability.timing import timed

class TestStructuredFormatter:
    def test_format_returns_json(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="hello", args=(), exc_info=None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "hello"
        assert parsed["logger"] == "test"

    def test_format_with_exception(self):
        formatter = StructuredFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py",
            lineno=1, msg="error occurred", args=(), exc_info=exc_info
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_format_with_extra_data(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="with extra", args=(), exc_info=None
        )
        record.extra_data = {"key": "value"}
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["extra"] == {"key": "value"}


class TestSetupStructuredLogging:
    def test_returns_root_logger(self):
        logger = setup_structured_logging("DEBUG")
        assert logger.level == logging.DEBUG

    def test_default_level(self):
        logger = setup_structured_logging()
        assert logger.level == logging.INFO

    def test_handler_is_structured(self):
        logger = setup_structured_logging()
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, StructuredFormatter)


class TestMetricsCollector:
    def test_increment(self):
        m = MetricsCollector()
        m.increment("req_count")
        m.increment("req_count", 3)
        snap = m.snapshot()
        assert snap["counters"]["req_count"] == 4

    def test_observe(self):
        m = MetricsCollector()
        m.observe("latency", 0.1)
        m.observe("latency", 0.2)
        snap = m.snapshot()
        assert snap["histograms"]["latency"] == [0.1, 0.2]

    def test_gauge(self):
        m = MetricsCollector()
        m.gauge("temperature", 36.5)
        m.gauge("temperature", 37.0)
        snap = m.snapshot()
        assert snap["gauges"]["temperature"] == 37.0

    def test_reset(self):
        m = MetricsCollector()
        m.increment("x")
        m.observe("y", 1.0)
        m.gauge("z", 2.0)
        m.reset()
        snap = m.snapshot()
        assert snap["counters"] == {}
        assert snap["histograms"] == {}
        assert snap["gauges"] == {}

    def test_snapshot_returns_independent_copy(self):
        m = MetricsCollector()
        m.increment("a")
        snap = m.snapshot()
        m.increment("a")
        assert snap["counters"]["a"] == 1
        assert m.snapshot()["counters"]["a"] == 2


class TestGlobalMetricsSingleton:
    def test_singleton_exists(self):
        assert isinstance(metrics, MetricsCollector)

    def test_singleton_is_shared(self):
        from backend.observability.metrics import metrics as m2
        assert metrics is m2


class TestTimedDecorator:
    def test_records_execution_time(self):
        m = MetricsCollector()
        original_metrics = __import__("backend.observability.timing", fromlist=["metrics"])
        import backend.observability.timing as timing_mod
        old = timing_mod.metrics
        timing_mod.metrics = m
        try:
            @timed("test_func")
            def slow():
                time.sleep(0.01)
            slow()
            snap = m.snapshot()
            assert "test_func_duration_seconds" in snap["histograms"]
            assert len(snap["histograms"]["test_func_duration_seconds"]) == 1
            assert snap["histograms"]["test_func_duration_seconds"][0] >= 0.01
        finally:
            timing_mod.metrics = old

    def test_preserves_return_value(self):
        @timed("noop")
        def add(a, b):
            return a + b
        assert add(2, 3) == 5

    def test_preserves_function_name(self):
        @timed("name_test")
        def my_func():
            pass
        assert my_func.__name__ == "my_func"