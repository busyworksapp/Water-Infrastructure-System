"""Real-time event correlation engine for complex pattern detection."""
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from dataclasses import dataclass, field

from ..models.alert import Alert, AlertType, AlertSeverity
from ..models.sensor import Sensor, SensorReading

logger = logging.getLogger(__name__)


@dataclass
class EventPattern:
    """Represents a complex event pattern to detect."""
    pattern_id: str
    name: str
    event_types: List[str]
    time_window_seconds: int
    min_occurrences: int
    spatial_radius_meters: Optional[float] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    description: str = ""
    actions: List[str] = field(default_factory=list)


class EventCorrelationEngine:
    """
    Advanced event correlation engine for detecting complex patterns
    across multiple sensors and time windows.
    """
    
    def __init__(self, max_events_per_sensor: int = 1000):
        self.max_events_per_sensor = max_events_per_sensor
        self.event_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_events_per_sensor))
        self.patterns: Dict[str, EventPattern] = {}
        self.correlation_cache: Dict[str, datetime] = {}
        self._initialize_default_patterns()
    
    def _initialize_default_patterns(self):
        """Initialize default correlation patterns."""
        
        # Cascade failure pattern
        self.register_pattern(EventPattern(
            pattern_id="cascade_failure",
            name="Cascade Failure Detection",
            event_types=["pressure_drop", "flow_irregularity"],
            time_window_seconds=300,  # 5 minutes
            min_occurrences=3,
            spatial_radius_meters=5000,
            severity=AlertSeverity.CRITICAL,
            description="Multiple sensors showing failures in sequence",
            actions=["notify_emergency", "activate_backup_systems"]
        ))
        
        # Widespread pressure drop
        self.register_pattern(EventPattern(
            pattern_id="widespread_pressure_drop",
            name="Widespread Pressure Drop",
            event_types=["pressure_anomaly", "pressure_drop"],
            time_window_seconds=600,  # 10 minutes
            min_occurrences=5,
            spatial_radius_meters=10000,
            severity=AlertSeverity.HIGH,
            description="Pressure drops detected across wide area",
            actions=["check_main_supply", "notify_operations"]
        ))
        
        # Coordinated sensor failure
        self.register_pattern(EventPattern(
            pattern_id="coordinated_failure",
            name="Coordinated Sensor Failure",
            event_types=["sensor_offline", "communication_loss"],
            time_window_seconds=180,  # 3 minutes
            min_occurrences=4,
            severity=AlertSeverity.HIGH,
            description="Multiple sensors going offline simultaneously",
            actions=["check_network", "check_power_supply"]
        ))
        
        # Progressive leak pattern
        self.register_pattern(EventPattern(
            pattern_id="progressive_leak",
            name="Progressive Leak Pattern",
            event_types=["leak", "pressure_drop", "flow_irregularity"],
            time_window_seconds=1800,  # 30 minutes
            min_occurrences=3,
            spatial_radius_meters=2000,
            severity=AlertSeverity.HIGH,
            description="Leak indicators progressing along pipeline",
            actions=["isolate_section", "dispatch_crew"]
        ))
        
        # Water hammer detection
        self.register_pattern(EventPattern(
            pattern_id="water_hammer",
            name="Water Hammer Event",
            event_types=["pressure_spike", "pressure_anomaly"],
            time_window_seconds=60,  # 1 minute
            min_occurrences=2,
            spatial_radius_meters=3000,
            severity=AlertSeverity.MEDIUM,
            description="Rapid pressure fluctuations indicating water hammer",
            actions=["check_valves", "reduce_flow_rate"]
        ))
    
    def register_pattern(self, pattern: EventPattern):
        """Register a new correlation pattern."""
        self.patterns[pattern.pattern_id] = pattern
        logger.info(f"Registered pattern: {pattern.name}")
    
    def add_event(
        self, 
        sensor_id: str, 
        event_type: str, 
        timestamp: datetime,
        metadata: Optional[Dict] = None
    ):
        """Add an event to the correlation buffer."""
        event = {
            "sensor_id": sensor_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        self.event_buffer[sensor_id].append(event)
        
        # Check for pattern matches
        self._check_patterns(event)
    
    def _check_patterns(self, new_event: Dict):
        """Check if new event triggers any correlation patterns."""
        for pattern_id, pattern in self.patterns.items():
            if new_event["event_type"] in pattern.event_types:
                match = self._evaluate_pattern(pattern, new_event)
                if match:
                    self._handle_pattern_match(pattern, match)
    
    def _evaluate_pattern(
        self, 
        pattern: EventPattern, 
        trigger_event: Dict
    ) -> Optional[Dict]:
        """Evaluate if a pattern is matched."""
        cutoff_time = trigger_event["timestamp"] - timedelta(seconds=pattern.time_window_seconds)
        
        # Collect relevant events within time window
        relevant_events = []
        sensor_ids = set()
        
        for sensor_id, events in self.event_buffer.items():
            for event in events:
                if (event["event_type"] in pattern.event_types and
                    event["timestamp"] >= cutoff_time and
                    event["timestamp"] <= trigger_event["timestamp"]):
                    relevant_events.append(event)
                    sensor_ids.add(sensor_id)
        
        # Check if minimum occurrences met
        if len(relevant_events) < pattern.min_occurrences:
            return None
        
        # Check spatial correlation if required
        if pattern.spatial_radius_meters:
            if not self._check_spatial_correlation(
                relevant_events, 
                pattern.spatial_radius_meters
            ):
                return None
        
        # Pattern matched
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_name": pattern.name,
            "matched_events": relevant_events,
            "sensor_count": len(sensor_ids),
            "time_span_seconds": (
                max(e["timestamp"] for e in relevant_events) -
                min(e["timestamp"] for e in relevant_events)
            ).total_seconds(),
            "trigger_event": trigger_event
        }
    
    def _check_spatial_correlation(
        self, 
        events: List[Dict], 
        max_radius_meters: float
    ) -> bool:
        """Check if events are spatially correlated."""
        # This would require sensor location data
        # Simplified implementation - assume correlation if multiple sensors
        unique_sensors = len(set(e["sensor_id"] for e in events))
        return unique_sensors >= 2
    
    def _handle_pattern_match(self, pattern: EventPattern, match: Dict):
        """Handle a detected pattern match."""
        # Check cooldown to avoid duplicate alerts
        cache_key = f"{pattern.pattern_id}_{match['trigger_event']['sensor_id']}"
        
        if cache_key in self.correlation_cache:
            last_alert = self.correlation_cache[cache_key]
            if (datetime.utcnow() - last_alert).total_seconds() < 300:  # 5 min cooldown
                return
        
        self.correlation_cache[cache_key] = datetime.utcnow()
        
        logger.warning(
            f"Pattern detected: {pattern.name} - "
            f"{match['sensor_count']} sensors affected"
        )
        
        # Trigger actions
        for action in pattern.actions:
            self._execute_action(action, pattern, match)
    
    def _execute_action(self, action: str, pattern: EventPattern, match: Dict):
        """Execute a correlation action."""
        if action == "notify_emergency":
            logger.critical(f"EMERGENCY: {pattern.name} detected")
            # Send emergency notifications
        
        elif action == "activate_backup_systems":
            logger.warning("Activating backup systems")
            # Trigger backup system activation
        
        elif action == "check_main_supply":
            logger.info("Checking main water supply")
            # Queue inspection task
        
        elif action == "notify_operations":
            logger.info("Notifying operations team")
            # Send notification to operations
        
        elif action == "check_network":
            logger.info("Checking network connectivity")
            # Run network diagnostics
        
        elif action == "check_power_supply":
            logger.info("Checking power supply")
            # Check power status
        
        elif action == "isolate_section":
            logger.warning("Isolating affected pipeline section")
            # Trigger valve closure
        
        elif action == "dispatch_crew":
            logger.info("Dispatching maintenance crew")
            # Create maintenance ticket
        
        elif action == "check_valves":
            logger.info("Checking valve status")
            # Query valve sensors
        
        elif action == "reduce_flow_rate":
            logger.info("Reducing flow rate")
            # Adjust pump settings
    
    def get_active_correlations(self, time_window_minutes: int = 60) -> List[Dict]:
        """Get currently active event correlations."""
        cutoff = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        active = []
        for pattern_id, pattern in self.patterns.items():
            # Count recent events matching this pattern
            event_count = 0
            affected_sensors = set()
            
            for sensor_id, events in self.event_buffer.items():
                for event in events:
                    if (event["event_type"] in pattern.event_types and
                        event["timestamp"] >= cutoff):
                        event_count += 1
                        affected_sensors.add(sensor_id)
            
            if event_count >= pattern.min_occurrences:
                active.append({
                    "pattern_id": pattern_id,
                    "pattern_name": pattern.name,
                    "event_count": event_count,
                    "affected_sensors": len(affected_sensors),
                    "severity": pattern.severity.value,
                    "description": pattern.description
                })
        
        return active
    
    def get_event_timeline(
        self, 
        sensor_id: Optional[str] = None, 
        minutes: int = 60
    ) -> List[Dict]:
        """Get event timeline for analysis."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        timeline = []
        
        if sensor_id:
            events = self.event_buffer.get(sensor_id, [])
            timeline = [
                e for e in events 
                if e["timestamp"] >= cutoff
            ]
        else:
            for sensor_id, events in self.event_buffer.items():
                timeline.extend([
                    e for e in events 
                    if e["timestamp"] >= cutoff
                ])
        
        return sorted(timeline, key=lambda x: x["timestamp"], reverse=True)
    
    def clear_old_events(self, hours: int = 24):
        """Clear events older than specified hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        for sensor_id in list(self.event_buffer.keys()):
            events = self.event_buffer[sensor_id]
            # Remove old events
            while events and events[0]["timestamp"] < cutoff:
                events.popleft()
            
            # Remove empty buffers
            if not events:
                del self.event_buffer[sensor_id]
        
        logger.info(f"Cleared events older than {hours} hours")
    
    def get_statistics(self) -> Dict:
        """Get correlation engine statistics."""
        total_events = sum(len(events) for events in self.event_buffer.values())
        
        event_types = defaultdict(int)
        for events in self.event_buffer.values():
            for event in events:
                event_types[event["event_type"]] += 1
        
        return {
            "total_sensors_tracked": len(self.event_buffer),
            "total_events_buffered": total_events,
            "registered_patterns": len(self.patterns),
            "event_types": dict(event_types),
            "cache_size": len(self.correlation_cache)
        }


# Global correlation engine instance
correlation_engine = EventCorrelationEngine()
