"""
Data Quality Monitoring Module

Monitors data quality metrics and alerts on issues:
- Packet loss rate
- Capture rate
- GPS fix quality
- Interpolation confidence
- Storage health
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Data quality alert."""
    level: AlertLevel
    metric_name: str
    message: str
    timestamp_ns: int
    current_value: float
    threshold: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSnapshot:
    """Snapshot of metric values."""
    timestamp_ns: int
    timestamp_dt: datetime
    metrics: Dict[str, float]


class DataQualityMonitor:
    """Monitor data quality metrics and generate alerts.

    Usage:
        monitor = DataQualityMonitor()

        # Configure thresholds
        monitor.set_threshold("packet_loss_rate", 0.1, AlertLevel.ERROR)

        # Update metrics
        monitor.update_metric("packet_loss_rate", 0.05)

        # Check for alerts
        alerts = monitor.get_alerts()
    """

    def __init__(
        self,
        stats_window_seconds: int = 60,
        alert_cooldown_seconds: int = 300,
    ):
        """Initialize data quality monitor.

        Args:
            stats_window_seconds: Time window for rolling statistics
            alert_cooldown_seconds: Cooldown between repeated alerts
        """
        self.stats_window_seconds = stats_window_seconds
        self.alert_cooldown_seconds = alert_cooldown_seconds

        # Metric buffers (time-series history)
        self.metric_history: Dict[str, deque] = {}
        self.max_history_size = 3600  # Keep 1 hour of 1-second samples

        # Thresholds
        self.thresholds: Dict[str, Dict[str, Any]] = {}

        # Alerts
        self.alerts: List[Alert] = []
        self.last_alert_time: Dict[str, int] = {}

        # Statistics
        self.stats = {
            "total_metrics_updated": 0,
            "alerts_generated": 0,
            "alerts_cleared": 0,
        }

    def set_threshold(
        self,
        metric_name: str,
        threshold_value: float,
        level: AlertLevel = AlertLevel.WARNING,
        direction: str = "above",
    ) -> None:
        """Set alert threshold for metric.

        Args:
            metric_name: Name of metric
            threshold_value: Threshold value
            level: Alert level when threshold exceeded
            direction: "above" or "below" for threshold check
        """
        self.thresholds[metric_name] = {
            "value": threshold_value,
            "level": level,
            "direction": direction,
        }

    def update_metric(self, metric_name: str, value: float) -> None:
        """Update metric value and check thresholds.

        Args:
            metric_name: Name of metric
            value: Current value
        """
        now_ns = int(time.time() * 1e9)
        now = time.time()

        # Initialize history if needed
        if metric_name not in self.metric_history:
            self.metric_history[metric_name] = deque(maxlen=self.max_history_size)

        # Add to history
        self.metric_history[metric_name].append((now, value))

        # Update stats
        self.stats["total_metrics_updated"] += 1

        # Check thresholds
        if metric_name in self.thresholds:
            self._check_threshold(metric_name, value, now_ns)

    def _check_threshold(self, metric_name: str, value: float, now_ns: int) -> None:
        """Check if metric exceeds threshold."""
        threshold_config = self.thresholds[metric_name]
        threshold_value = threshold_config["value"]
        level = threshold_config["level"]
        direction = threshold_config["direction"]

        exceeded = False
        if direction == "above" and value > threshold_value:
            exceeded = True
        elif direction == "below" and value < threshold_value:
            exceeded = True

        if exceeded:
            # Check cooldown
            last_alert = self.last_alert_time.get(metric_name, 0)
            age_seconds = (now_ns - last_alert) / 1e9

            if age_seconds >= self.alert_cooldown_seconds:
                # Generate alert
                alert = Alert(
                    level=level,
                    metric_name=metric_name,
                    message=f"{metric_name} {direction} threshold: {value:.4f} {direction} {threshold_value:.4f}",
                    timestamp_ns=now_ns,
                    current_value=value,
                    threshold=threshold_value,
                )

                self.alerts.append(alert)
                self.last_alert_time[metric_name] = now_ns
                self.stats["alerts_generated"] += 1

    def get_metric_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for metric.

        Args:
            metric_name: Name of metric

        Returns:
            Dictionary with min, max, mean, std, current
        """
        if metric_name not in self.metric_history:
            return None

        history = self.metric_history[metric_name]
        if not history:
            return None

        values = [v for _, v in history]

        return {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "count": len(values),
            "current": values[-1],
        }

    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        since_ns: Optional[int] = None,
    ) -> List[Alert]:
        """Get alerts.

        Args:
            level: Filter by alert level
            since_ns: Only get alerts since timestamp

        Returns:
            List of alerts
        """
        alerts = self.alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        if since_ns:
            alerts = [a for a in alerts if a.timestamp_ns >= since_ns]

        return alerts

    def clear_old_alerts(self, older_than_seconds: int = 3600) -> int:
        """Clear old alerts.

        Args:
            older_than_seconds: Clear alerts older than this

        Returns:
            Number of alerts cleared
        """
        now_ns = int(time.time() * 1e9)
        cutoff_ns = now_ns - (older_than_seconds * 1e9)

        original_count = len(self.alerts)
        self.alerts = [a for a in self.alerts if a.timestamp_ns >= cutoff_ns]
        cleared = original_count - len(self.alerts)

        self.stats["alerts_cleared"] += cleared

        return cleared

    def get_health_score(self) -> float:
        """Calculate overall system health score.

        Returns:
            Health score from 0.0 (bad) to 1.0 (good)
        """
        if not self.metric_history:
            return 1.0

        # Check all metrics with thresholds
        total_metrics = 0
        passing_metrics = 0

        for metric_name, config in self.thresholds.items():
            if metric_name not in self.metric_history:
                continue

            history = self.metric_history[metric_name]
            if not history:
                continue

            total_metrics += 1
            current_value = history[-1][1]
            threshold_value = config["value"]

            # Check if passing
            direction = config["direction"]
            if direction == "above":
                if current_value <= threshold_value:
                    passing_metrics += 1
            else:  # below
                if current_value >= threshold_value:
                    passing_metrics += 1

        if total_metrics == 0:
            return 1.0

        return passing_metrics / total_metrics

    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        return {
            **self.stats,
            "active_alerts": len(self.alerts),
            "health_score": self.get_health_score(),
            "metrics_monitored": len(self.metric_history),
            "thresholds_configured": len(self.thresholds),
        }


class CaptureQualityTracker:
    """Track quality of network packet capture."""

    def __init__(self, monitor: DataQualityMonitor):
        """Initialize capture quality tracker.

        Args:
            monitor: Data quality monitor instance
        """
        self.monitor = monitor
        self.expected_rate_hz = 15.0  # Furuno default
        self.last_capture_time = None
        self.packets_captured = 0
        self.packets_dropped = 0

        # Configure default thresholds
        self.monitor.set_threshold("packet_loss_rate", 0.1, AlertLevel.ERROR, "above")
        self.monitor.set_threshold("capture_rate_hz", 14.0, AlertLevel.WARNING, "below")

    def update_capture_stats(
        self,
        packets_captured: int,
        packets_dropped: int,
        capture_rate_hz: float,
    ) -> None:
        """Update capture statistics.

        Args:
            packets_captured: Total packets captured
            packets_dropped: Total packets dropped
            capture_rate_hz: Current capture rate in Hz
        """
        self.packets_captured = packets_captured
        self.packets_dropped = packets_dropped

        # Calculate packet loss rate
        total_packets = packets_captured + packets_dropped
        if total_packets > 0:
            loss_rate = 100.0 * packets_dropped / total_packets
            self.monitor.update_metric("packet_loss_rate", loss_rate)

        # Update capture rate
        self.monitor.update_metric("capture_rate_hz", capture_rate_hz)


class GPSQualityTracker:
    """Track quality of GPS data."""

    def __init__(self, monitor: DataQualityMonitor):
        """Initialize GPS quality tracker.

        Args:
            monitor: Data quality monitor instance
        """
        self.monitor = monitor

        # Configure default thresholds
        self.monitor.set_threshold("gps_fix_quality", 1, AlertLevel.ERROR, "below")
        self.monitor.set_threshold("gps_satellites", 4, AlertLevel.WARNING, "below")
        self.monitor.set_threshold("gps_hdop", 2.0, AlertLevel.WARNING, "above")

    def update_gps_stats(
        self,
        fix_quality: int,
        satellites: int,
        hdop: float,
    ) -> None:
        """Update GPS statistics.

        Args:
            fix_quality: GPS fix quality (0=Invalid, 1=GPS, 2=DGPS)
            satellites: Number of satellites
            hdop: Horizontal dilution of precision
        """
        self.monitor.update_metric("gps_fix_quality", float(fix_quality))
        self.monitor.update_metric("gps_satellites", float(satellites))
        self.monitor.update_metric("gps_hdop", hdop)


class InterpolationQualityTracker:
    """Track quality of position interpolation."""

    def __init__(self, monitor: DataQualityMonitor):
        """Initialize interpolation quality tracker.

        Args:
            monitor: Data quality monitor instance
        """
        self.monitor = monitor

        # Configure default thresholds
        self.monitor.set_threshold("interpolation_confidence", 0.8, AlertLevel.WARNING, "below")
        self.monitor.set_threshold("interpolation_age_ms", 1000, AlertLevel.WARNING, "above")

    def update_interpolation_stats(
        self,
        confidence: float,
        age_ms: float,
        method: str,
    ) -> None:
        """Update interpolation statistics.

        Args:
            confidence: Interpolation confidence (0-1)
            age_ms: Age of GPS data used (milliseconds)
            method: Interpolation method
        """
        self.monitor.update_metric("interpolation_confidence", confidence)
        self.monitor.update_metric("interpolation_age_ms", age_ms)


if __name__ == "__main__":
    # Test data quality monitoring
    print("Testing data quality monitoring...")

    monitor = DataQualityMonitor()

    # Set thresholds
    monitor.set_threshold("packet_loss_rate", 0.1, AlertLevel.ERROR)
    monitor.set_threshold("capture_rate_hz", 14.0, AlertLevel.WARNING, "below")

    # Simulate metrics
    for i in range(100):
        # Good performance
        monitor.update_metric("packet_loss_rate", 0.05)
        monitor.update_metric("capture_rate_hz", 15.0)

    # Simulate issue
    monitor.update_metric("packet_loss_rate", 0.15)  # Exceeds threshold
    monitor.update_metric("capture_rate_hz", 12.0)  # Below threshold

    # Get alerts
    alerts = monitor.get_alerts()
    print(f"Alerts generated: {len(alerts)}")
    for alert in alerts:
        print(f"  [{alert.level.value.upper()}] {alert.message}")

    # Get health score
    health = monitor.get_health_score()
    print(f"Health score: {health:.2f}")

    print("Data quality monitoring test complete.")
