"""
Data Models for Maritime Situation Awareness Layer
Production-ready data structures with full type safety
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import json


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SensorType(Enum):
    """Available sensor types"""
    AIS = "ais"
    RADAR = "radar"
    GPS = "gps"
    WEATHER = "weather"
    ENGINE = "engine"
    CAMERA = "camera"
    CHART = "chart"
    TIDE = "tide"
    CURRENT = "current"


class AnomalyType(Enum):
    """Types of detectable anomalies"""
    TRAJECTORY_DEVIATION = "trajectory_deviation"
    SPEED_ANOMALY = "speed_anomaly"
    SENSOR_MISMATCH = "sensor_mismatch"
    COLLISION_RISK = "collision_risk"
    SUDDEN_MANEUVER = "sudden_maneuver"
    SENSOR_DEGRADATION = "sensor_degradation"
    DATA_QUALITY_ISSUE = "data_quality_issue"


class SpoofingType(Enum):
    """Types of spoofing attacks"""
    GPS_SPOOFING = "gps_spoofing"
    AIS_SPOOFING = "ais_spoofing"
    MULTI_SENSOR_SPOOFING = "multi_sensor_spoofing"


@dataclass
class Position:
    """Geographic position"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VesselState:
    """Complete vessel state"""
    position: Position
    speed: float  # knots
    course: float  # degrees (0-360)
    heading: float  # degrees (0-360)
    rate_of_turn: float  # degrees per minute
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class Target:
    """Tracked target vessel"""
    target_id: str
    position: Position
    speed: float
    course: float
    cpa: float  # Closest Point of Approach (nautical miles)
    tcpa: float  # Time to CPA (minutes)
    distance: float  # Current distance (nautical miles)
    vessel_type: Optional[str] = None
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FusedData:
    """Fused sensor data output"""
    vessel_state: VesselState
    targets: List[Target]
    environment: Dict[str, Any]
    quality_scores: Dict[str, float]
    fusion_confidence: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vessel_state': self.vessel_state.to_dict(),
            'targets': [t.to_dict() for t in self.targets],
            'environment': self.environment,
            'quality_scores': self.quality_scores,
            'fusion_confidence': self.fusion_confidence,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: float  # 0.0 to 1.0
    description: str
    affected_sensors: List[str]
    detected_at: datetime
    location: Optional[Position] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_alert_level(self) -> AlertLevel:
        """Convert severity to alert level"""
        if self.severity >= 0.8:
            return AlertLevel.CRITICAL
        elif self.severity >= 0.5:
            return AlertLevel.WARNING
        else:
            return AlertLevel.INFO
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'anomaly_id': self.anomaly_id,
            'anomaly_type': self.anomaly_type.value,
            'severity': self.severity,
            'description': self.description,
            'affected_sensors': self.affected_sensors,
            'detected_at': self.detected_at.isoformat(),
            'location': self.location.to_dict() if self.location else None,
            'metadata': self.metadata,
            'alert_level': self.to_alert_level().value
        }


@dataclass
class SpoofingAlert:
    """Spoofing detection alert"""
    alert_id: str
    spoofing_type: SpoofingType
    confidence: float  # 0.0 to 1.0
    description: str
    affected_sensors: List[str]
    evidence: Dict[str, Any]
    detected_at: datetime
    recommended_action: str
    
    def to_alert_level(self) -> AlertLevel:
        """Always returns EMERGENCY for spoofing"""
        if self.confidence >= 0.7:
            return AlertLevel.EMERGENCY
        elif self.confidence >= 0.5:
            return AlertLevel.CRITICAL
        else:
            return AlertLevel.WARNING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'spoofing_type': self.spoofing_type.value,
            'confidence': self.confidence,
            'description': self.description,
            'affected_sensors': self.affected_sensors,
            'evidence': self.evidence,
            'detected_at': self.detected_at.isoformat(),
            'recommended_action': self.recommended_action,
            'alert_level': self.to_alert_level().value
        }


@dataclass
class Uncertainty:
    """Uncertainty estimate"""
    parameter: str
    mean_value: float
    std_deviation: float
    confidence_interval: Tuple[float, float]
    reliability: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'parameter': self.parameter,
            'mean_value': self.mean_value,
            'std_deviation': self.std_deviation,
            'confidence_interval': list(self.confidence_interval),
            'reliability': self.reliability
        }


@dataclass
class Alert:
    """System alert"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'metadata': self.metadata,
            'acknowledged': self.acknowledged
        }


@dataclass
class SituationAwarenessOutput:
    """Complete situational awareness assessment"""
    timestamp: datetime
    fused_data: FusedData
    anomalies: List[Anomaly]
    uncertainties: Dict[str, Uncertainty]
    spoofing_alerts: List[SpoofingAlert]
    overall_confidence: float
    alerts: List[Alert]
    system_status: Dict[str, str]
    
    def has_spoofing(self) -> bool:
        """Check if spoofing detected"""
        return len(self.spoofing_alerts) > 0
    
    def get_critical_alerts(self) -> List[Alert]:
        """Get critical and emergency alerts"""
        return [a for a in self.alerts 
                if a.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'fused_data': self.fused_data.to_dict(),
            'anomalies': [a.to_dict() for a in self.anomalies],
            'uncertainties': {k: v.to_dict() for k, v in self.uncertainties.items()},
            'spoofing_alerts': [s.to_dict() for s in self.spoofing_alerts],
            'overall_confidence': self.overall_confidence,
            'alerts': [a.to_dict() for a in self.alerts],
            'system_status': self.system_status,
            'has_spoofing': self.has_spoofing(),
            'critical_alert_count': len(self.get_critical_alerts())
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
