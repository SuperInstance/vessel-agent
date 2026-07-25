"""
Tests for Data Quality Monitoring Module

Test suite for data quality monitoring and alerting.
"""

import pytest
import time

from vessel_agent.monitoring.data_quality import (
    AlertLevel,
    Alert,
    MetricSnapshot,
    DataQualityMonitor,
    CaptureQualityTracker,
    GPSQualityTracker,
    InterpolationQualityTracker,
)


class TestAlertLevel:
    """Tests for AlertLevel enum."""

    def test_levels(self):
        """Test alert levels exist."""
        assert AlertLevel.INFO
        assert AlertLevel.WARNING
        assert AlertLevel.ERROR
        assert AlertLevel.CRITICAL


class TestAlert:
    """Tests for Alert dataclass."""

    def test_creation(self):
        """Test creating alert."""
        alert = Alert(
            level=AlertLevel.WARNING,
            metric_name="packet_loss_rate",
            message="Packet loss exceeded threshold",
            timestamp_ns=1721741135000000000,
            current_value=0.15,
            threshold=0.1,
        )

        assert alert.level == AlertLevel.WARNING
        assert alert.metric_name == "packet_loss_rate"
        assert alert.current_value == 0.15
        assert alert.threshold == 0.1


class TestDataQualityMonitor:
    """Tests for DataQualityMonitor class."""

    def test_init(self):
        """Test monitor initialization."""
        monitor = DataQualityMonitor()

        assert monitor.stats_window_seconds == 60
        assert monitor.alert_cooldown_seconds == 300
        assert len(monitor.metric_history) == 0
        assert len(monitor.alerts) == 0

    def test_set_threshold(self):
        """Test setting threshold."""
        monitor = DataQualityMonitor()

        monitor.set_threshold(
            metric_name="packet_loss_rate",
            threshold_value=0.1,
            level=AlertLevel.ERROR,
        )

        assert "packet_loss_rate" in monitor.thresholds
        assert monitor.thresholds["packet_loss_rate"]["value"] == 0.1
        assert monitor.thresholds["packet_loss_rate"]["level"] == AlertLevel.ERROR

    def test_update_metric(self):
        """Test updating metric."""
        monitor = DataQualityMonitor()

        monitor.update_metric("test_metric", 1.0)
        monitor.update_metric("test_metric", 2.0)
        monitor.update_metric("test_metric", 3.0)

        assert "test_metric" in monitor.metric_history
        assert len(monitor.metric_history["test_metric"]) == 3
        assert monitor.stats["total_metrics_updated"] == 3

    def test_threshold_alert_above(self):
        """Test alert when metric exceeds threshold."""
        monitor = DataQualityMonitor()

        monitor.set_threshold("test_metric", 10.0, AlertLevel.WARNING, "above")

        # Below threshold - no alert
        monitor.update_metric("test_metric", 5.0)
        assert len(monitor.get_alerts()) == 0

        # Above threshold - alert
        monitor.update_metric("test_metric", 15.0)
        alerts = monitor.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING
        assert alerts[0].metric_name == "test_metric"

    def test_threshold_alert_below(self):
        """Test alert when metric below threshold."""
        monitor = DataQualityMonitor()

        monitor.set_threshold("capture_rate", 10.0, AlertLevel.ERROR, "below")

        # Above threshold - no alert
        monitor.update_metric("capture_rate", 15.0)
        assert len(monitor.get_alerts()) == 0

        # Below threshold - alert
        monitor.update_metric("capture_rate", 5.0)
        alerts = monitor.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.ERROR

    def test_alert_cooldown(self):
        """Test alert cooldown prevents spam."""
        monitor = DataQualityMonitor(alert_cooldown_seconds=1.0)

        monitor.set_threshold("test_metric", 10.0, AlertLevel.WARNING, "above")

        # First alert
        monitor.update_metric("test_metric", 15.0)
        assert len(monitor.get_alerts()) == 1

        # Immediate update - should not alert (cooldown)
        monitor.update_metric("test_metric", 15.0)
        assert len(monitor.get_alerts()) == 1

    def test_get_metric_stats(self):
        """Test getting metric statistics."""
        monitor = DataQualityMonitor()

        monitor.update_metric("test_metric", 10.0)
        monitor.update_metric("test_metric", 20.0)
        monitor.update_metric("test_metric", 30.0)

        stats = monitor.get_metric_stats("test_metric")

        assert stats is not None
        assert stats["min"] == 10.0
        assert stats["max"] == 30.0
        assert stats["mean"] == 20.0
        assert stats["current"] == 30.0
        assert stats["count"] == 3

    def test_get_alerts_filter_by_level(self):
        """Test filtering alerts by level."""
        monitor = DataQualityMonitor()

        monitor.set_threshold("metric1", 10.0, AlertLevel.WARNING, "above")
        monitor.set_threshold("metric2", 10.0, AlertLevel.ERROR, "above")

        monitor.update_metric("metric1", 15.0)
        monitor.update_metric("metric2", 15.0)

        # All alerts
        all_alerts = monitor.get_alerts()
        assert len(all_alerts) == 2

        # Filter by level
        error_alerts = monitor.get_alerts(level=AlertLevel.ERROR)
        assert len(error_alerts) == 1
        assert error_alerts[0].level == AlertLevel.ERROR

    def test_clear_old_alerts(self):
        """Test clearing old alerts."""
        monitor = DataQualityMonitor(alert_cooldown_seconds=0)

        monitor.set_threshold("test_metric", 10.0, AlertLevel.WARNING, "above")
        monitor.update_metric("test_metric", 15.0)

        assert len(monitor.get_alerts()) == 1

        # Clear all (older_than 0 seconds)
        cleared = monitor.clear_old_alerts(older_than_seconds=0)

        assert cleared == 1
        assert len(monitor.get_alerts()) == 0

    def test_health_score(self):
        """Test health score calculation."""
        monitor = DataQualityMonitor()

        # No thresholds - perfect health
        assert monitor.get_health_score() == 1.0

        # Add threshold and good metric
        monitor.set_threshold("test_metric", 10.0, AlertLevel.WARNING, "above")
        monitor.update_metric("test_metric", 5.0)  # Below threshold = good

        # Good health
        health = monitor.get_health_score()
        assert health == 1.0

        # Bad metric
        monitor.update_metric("test_metric", 15.0)  # Above threshold = bad

        # Reduced health
        health = monitor.get_health_score()
        assert health < 1.0

    def test_get_stats(self):
        """Test getting monitor statistics."""
        monitor = DataQualityMonitor()

        monitor.set_threshold("test_metric", 10.0, AlertLevel.WARNING, "above")
        monitor.update_metric("test_metric", 15.0)

        stats = monitor.get_stats()

        assert "total_metrics_updated" in stats
        assert "alerts_generated" in stats
        assert "health_score" in stats
        assert stats["metrics_monitored"] == 1
        assert stats["thresholds_configured"] == 1


class TestCaptureQualityTracker:
    """Tests for CaptureQualityTracker class."""

    def test_update_capture_stats(self):
        """Test updating capture statistics."""
        monitor = DataQualityMonitor()
        tracker = CaptureQualityTracker(monitor)

        tracker.update_capture_stats(
            packets_captured=1000,
            packets_dropped=5,
            capture_rate_hz=14.5,
        )

        # Check metrics were updated
        loss_rate = monitor.get_metric_stats("packet_loss_rate")
        assert loss_rate is not None
        assert loss_rate["current"] == pytest.approx(0.5, rel=0.1)  # 5/1005

        capture_rate = monitor.get_metric_stats("capture_rate_hz")
        assert capture_rate is not None
        assert capture_rate["current"] == 14.5


class TestGPSQualityTracker:
    """Tests for GPSQualityTracker class."""

    def test_update_gps_stats(self):
        """Test updating GPS statistics."""
        monitor = DataQualityMonitor()
        tracker = GPSQualityTracker(monitor)

        tracker.update_gps_stats(
            fix_quality=1,
            satellites=8,
            hdop=1.2,
        )

        # Check metrics were updated
        fix = monitor.get_metric_stats("gps_fix_quality")
        assert fix is not None
        assert fix["current"] == 1.0

        sats = monitor.get_metric_stats("gps_satellites")
        assert sats is not None
        assert sats["current"] == 8.0

        hdop = monitor.get_metric_stats("gps_hdop")
        assert hdop is not None
        assert hdop["current"] == 1.2


class TestInterpolationQualityTracker:
    """Tests for InterpolationQualityTracker class."""

    def test_update_interpolation_stats(self):
        """Test updating interpolation statistics."""
        monitor = DataQualityMonitor()
        tracker = InterpolationQualityTracker(monitor)

        tracker.update_interpolation_stats(
            confidence=0.95,
            age_ms=250,
            method="linear",
        )

        # Check metrics were updated
        conf = monitor.get_metric_stats("interpolation_confidence")
        assert conf is not None
        assert conf["current"] == 0.95

        age = monitor.get_metric_stats("interpolation_age_ms")
        assert age is not None
        assert age["current"] == 250.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
