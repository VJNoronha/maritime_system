"""
Anomaly Detection Module
Detects anomalies in sensor data and vessel behavior using rule-based algorithms
No ML required - uses statistical methods and maritime domain rules
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math
import uuid


class AnomalyDetector:
    """
    Detects anomalies using statistical methods and maritime rules.
    Monitors for trajectory deviations, sensor mismatches, collision risks, etc.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger('AnomalyDetector')
        
        # Thresholds for anomaly detection
        self.thresholds = {
            'speed_deviation': 5.0,  # knots
            'course_deviation': 30.0,  # degrees
            'sensor_mismatch': 0.002,  # ~200m position difference
            'collision_risk_distance': 2.0,  # nautical miles
            'collision_risk_tcpa': 10.0,  # minutes
            'sudden_maneuver_rot': 15.0,  # degrees per minute
            'speed_change_rate': 3.0,  # knots per minute
        }
        
        # State history for temporal analysis
        self.speed_history: List[float] = []
        self.course_history: List[float] = []
        self.position_history: List[tuple] = []
        self.max_history = 30
        
        self.logger.info("Anomaly Detector initialized")
    
    def detect(self, fused_data: Any, raw_sensor_data: Dict[str, Any]) -> List[Any]:
        """
        Detect anomalies in fused data and sensor readings.
        
        Args:
            fused_data: Fused sensor data
            raw_sensor_data: Raw sensor readings for comparison
        
        Returns:
            List of Anomaly objects
        """
        from models.data_models import Anomaly, AnomalyType, Position
        
        anomalies = []
        timestamp = datetime.now()
        
        # Update history
        self._update_history(fused_data.vessel_state)
        
        # 1. Check for trajectory deviations
        trajectory_anomalies = self._detect_trajectory_deviation(fused_data.vessel_state)
        anomalies.extend(trajectory_anomalies)
        
        # 2. Check for speed anomalies
        speed_anomalies = self._detect_speed_anomaly(fused_data.vessel_state)
        anomalies.extend(speed_anomalies)
        
        # 3. Check for sensor mismatches
        mismatch_anomalies = self._detect_sensor_mismatch(raw_sensor_data)
        anomalies.extend(mismatch_anomalies)
        
        # 4. Check for collision risks
        collision_anomalies = self._detect_collision_risk(
            fused_data.vessel_state, 
            fused_data.targets
        )
        anomalies.extend(collision_anomalies)
        
        # 5. Check for sudden maneuvers
        maneuver_anomalies = self._detect_sudden_maneuver(fused_data.vessel_state)
        anomalies.extend(maneuver_anomalies)
        
        # 6. Check for sensor degradation
        degradation_anomalies = self._detect_sensor_degradation(raw_sensor_data)
        anomalies.extend(degradation_anomalies)
        
        self.logger.debug(f"Detected {len(anomalies)} anomalies")
        
        return anomalies
    
    def _update_history(self, vessel_state: Any):
        """Update historical data"""
        self.speed_history.append(vessel_state.speed)
        self.course_history.append(vessel_state.course)
        self.position_history.append((
            vessel_state.position.latitude,
            vessel_state.position.longitude,
            datetime.now()
        ))
        
        # Maintain max history length
        if len(self.speed_history) > self.max_history:
            self.speed_history.pop(0)
        if len(self.course_history) > self.max_history:
            self.course_history.pop(0)
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)
    
    def _detect_trajectory_deviation(self, vessel_state: Any) -> List[Any]:
        """Detect if vessel deviates from expected trajectory"""
        from models.data_models import Anomaly, AnomalyType
        
        anomalies = []
        
        if len(self.position_history) < 3:
            return anomalies
        
        # Calculate expected position based on previous trajectory
        expected_lat, expected_lon = self._predict_position()
        
        actual_lat = vessel_state.position.latitude
        actual_lon = vessel_state.position.longitude
        
        # Calculate deviation
        deviation = self._haversine_distance(
            expected_lat, expected_lon, actual_lat, actual_lon
        )
        
        # Check if deviation is significant (> 500 meters)
        if deviation > 500:
            severity = min(1.0, deviation / 2000)  # Max at 2km
            
            anomaly = Anomaly(
                anomaly_id=f"traj_dev_{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.TRAJECTORY_DEVIATION,
                severity=severity,
                description=f"Vessel deviated {deviation:.0f}m from expected trajectory",
                affected_sensors=['gps', 'ais'],
                detected_at=datetime.now(),
                location=vessel_state.position,
                metadata={'deviation_meters': deviation}
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _predict_position(self) -> tuple:
        """Predict next position based on recent trajectory"""
        if len(self.position_history) < 2:
            return self.position_history[-1][:2]
        
        # Simple linear prediction
        lat1, lon1, t1 = self.position_history[-2]
        lat2, lon2, t2 = self.position_history[-1]
        
        time_diff = (t2 - t1).total_seconds()
        if time_diff == 0:
            return lat2, lon2
        
        # Extrapolate
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Predict 30 seconds ahead
        predicted_lat = lat2 + (dlat / time_diff) * 30
        predicted_lon = lon2 + (dlon / time_diff) * 30
        
        return predicted_lat, predicted_lon
    
    def _detect_speed_anomaly(self, vessel_state: Any) -> List[Any]:
        """Detect abnormal speed changes"""
        from models.data_models import Anomaly, AnomalyType
        
        anomalies = []
        
        if len(self.speed_history) < 2:
            return anomalies
        
        current_speed = vessel_state.speed
        avg_speed = sum(self.speed_history) / len(self.speed_history)
        
        # Check for sudden speed change
        speed_deviation = abs(current_speed - avg_speed)
        
        if speed_deviation > self.thresholds['speed_deviation']:
            severity = min(1.0, speed_deviation / 20.0)
            
            anomaly = Anomaly(
                anomaly_id=f"speed_anom_{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.SPEED_ANOMALY,
                severity=severity,
                description=f"Speed deviated {speed_deviation:.1f} knots from average",
                affected_sensors=['gps', 'engine'],
                detected_at=datetime.now(),
                location=vessel_state.position,
                metadata={
                    'current_speed': current_speed,
                    'average_speed': avg_speed,
                    'deviation': speed_deviation
                }
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_sensor_mismatch(self, raw_sensor_data: Dict[str, Any]) -> List[Any]:
        """Detect mismatches between sensors"""
        from models.data_models import Anomaly, AnomalyType, Position
        
        anomalies = []
        
        # Compare GPS and AIS positions
        if 'gps' in raw_sensor_data and 'ais' in raw_sensor_data:
            gps = raw_sensor_data['gps']
            ais = raw_sensor_data['ais']
            
            if all(k in gps for k in ['latitude', 'longitude']) and \
               all(k in ais for k in ['latitude', 'longitude']):
                
                distance = self._haversine_distance(
                    gps['latitude'], gps['longitude'],
                    ais['latitude'], ais['longitude']
                )
                
                # Mismatch threshold: 200 meters
                if distance > 200:
                    severity = min(1.0, distance / 1000)
                    
                    anomaly = Anomaly(
                        anomaly_id=f"sensor_mismatch_{uuid.uuid4().hex[:8]}",
                        anomaly_type=AnomalyType.SENSOR_MISMATCH,
                        severity=severity,
                        description=f"GPS and AIS positions differ by {distance:.0f}m",
                        affected_sensors=['gps', 'ais'],
                        detected_at=datetime.now(),
                        location=Position(gps['latitude'], gps['longitude']),
                        metadata={'distance_meters': distance}
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_collision_risk(self, vessel_state: Any, targets: List[Any]) -> List[Any]:
        """Detect collision risks with other vessels"""
        from models.data_models import Anomaly, AnomalyType
        
        anomalies = []
        
        for target in targets:
            # Check CPA (Closest Point of Approach)
            if target.cpa < self.thresholds['collision_risk_distance'] and \
               target.tcpa < self.thresholds['collision_risk_tcpa'] and \
               target.tcpa > 0:
                
                # Calculate severity based on CPA and TCPA
                cpa_factor = 1.0 - (target.cpa / self.thresholds['collision_risk_distance'])
                tcpa_factor = 1.0 - (target.tcpa / self.thresholds['collision_risk_tcpa'])
                severity = (cpa_factor + tcpa_factor) / 2
                
                anomaly = Anomaly(
                    anomaly_id=f"collision_{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.COLLISION_RISK,
                    severity=severity,
                    description=f"Collision risk with {target.name or target.target_id}: "
                               f"CPA {target.cpa:.2f}nm in {target.tcpa:.1f} min",
                    affected_sensors=['ais', 'radar'],
                    detected_at=datetime.now(),
                    location=target.position,
                    metadata={
                        'target_id': target.target_id,
                        'cpa': target.cpa,
                        'tcpa': target.tcpa,
                        'distance': target.distance
                    }
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_sudden_maneuver(self, vessel_state: Any) -> List[Any]:
        """Detect sudden maneuvers (high rate of turn)"""
        from models.data_models import Anomaly, AnomalyType
        
        anomalies = []
        
        if abs(vessel_state.rate_of_turn) > self.thresholds['sudden_maneuver_rot']:
            severity = min(1.0, abs(vessel_state.rate_of_turn) / 30.0)
            
            anomaly = Anomaly(
                anomaly_id=f"maneuver_{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.SUDDEN_MANEUVER,
                severity=severity,
                description=f"Sudden maneuver detected: ROT {vessel_state.rate_of_turn:.1f}°/min",
                affected_sensors=['ais', 'gps'],
                detected_at=datetime.now(),
                location=vessel_state.position,
                metadata={'rate_of_turn': vessel_state.rate_of_turn}
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_sensor_degradation(self, raw_sensor_data: Dict[str, Any]) -> List[Any]:
        """Detect sensor quality degradation"""
        from models.data_models import Anomaly, AnomalyType
        
        anomalies = []
        
        # Check if critical sensors are missing or have poor data
        critical_sensors = ['gps', 'ais', 'radar']
        
        for sensor in critical_sensors:
            if sensor not in raw_sensor_data or not raw_sensor_data[sensor]:
                anomaly = Anomaly(
                    anomaly_id=f"sensor_deg_{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.SENSOR_DEGRADATION,
                    severity=0.8,
                    description=f"Critical sensor {sensor.upper()} is not providing data",
                    affected_sensors=[sensor],
                    detected_at=datetime.now(),
                    metadata={'sensor': sensor}
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _haversine_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """Calculate distance between two positions in meters"""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
