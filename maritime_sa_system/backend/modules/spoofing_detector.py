"""
Spoofing Detection Module
Detects GPS and AIS spoofing attacks using multi-sensor cross-validation
No ML required - uses consistency checking and maritime domain knowledge
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math
import uuid


class SpoofingDetector:
    """
    Detects spoofing attacks by cross-validating sensor data and checking
    for physically impossible scenarios and inconsistencies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger('SpoofingDetector')
        
        # Detection thresholds
        self.thresholds = {
            'position_jump': 1000,  # meters - impossible instantaneous movement
            'speed_impossibility': 60.0,  # knots - unrealistic for most vessels
            'acceleration_limit': 5.0,  # knots per second
            'multi_sensor_mismatch': 500,  # meters between GPS/AIS/RADAR
            'time_inconsistency': 60,  # seconds - timestamp manipulation
        }
        
        # Track previous positions for jump detection
        self.previous_gps_position = None
        self.previous_ais_position = None
        self.last_update_time = None
        
        # Spoofing incident tracking
        self.spoofing_incidents: List[Dict[str, Any]] = []
        
        self.logger.info("Spoofing Detector initialized")
    
    def detect(
        self, 
        raw_sensor_data: Dict[str, Any], 
        fused_data: Any
    ) -> List[Any]:
        """
        Detect spoofing attempts in sensor data.
        
        Args:
            raw_sensor_data: Raw sensor readings
            fused_data: Fused data for cross-validation
        
        Returns:
            List of SpoofingAlert objects
        """
        from models.data_models import SpoofingAlert, SpoofingType
        
        alerts = []
        timestamp = datetime.now()
        
        # 1. Check for GPS spoofing
        gps_alerts = self._detect_gps_spoofing(raw_sensor_data)
        alerts.extend(gps_alerts)
        
        # 2. Check for AIS spoofing
        ais_alerts = self._detect_ais_spoofing(raw_sensor_data)
        alerts.extend(ais_alerts)
        
        # 3. Check for multi-sensor inconsistencies (strongest indicator)
        multi_alerts = self._detect_multi_sensor_spoofing(raw_sensor_data, fused_data)
        alerts.extend(multi_alerts)
        
        # 4. Check for time manipulation
        time_alerts = self._detect_time_manipulation(raw_sensor_data)
        alerts.extend(time_alerts)
        
        if alerts:
            self.logger.warning(f"⚠️  SPOOFING DETECTED: {len(alerts)} alerts")
            self._log_spoofing_incident(alerts)
        
        return alerts
    
    def _detect_gps_spoofing(self, raw_sensor_data: Dict[str, Any]) -> List[Any]:
        """Detect GPS spoofing through impossible movements"""
        from models.data_models import SpoofingAlert, SpoofingType
        
        alerts = []
        
        if 'gps' not in raw_sensor_data or not raw_sensor_data['gps']:
            return alerts
        
        gps = raw_sensor_data['gps']
        
        if 'latitude' not in gps or 'longitude' not in gps:
            return alerts
        
        current_lat = gps['latitude']
        current_lon = gps['longitude']
        current_time = datetime.now()
        
        # Check for position jump (teleportation)
        if self.previous_gps_position and self.last_update_time:
            prev_lat, prev_lon = self.previous_gps_position
            
            # Calculate distance moved
            distance = self._haversine_distance(
                prev_lat, prev_lon, current_lat, current_lon
            )
            
            # Calculate time elapsed
            time_diff = (current_time - self.last_update_time).total_seconds()
            
            if time_diff > 0:
                # Calculate implied speed
                implied_speed = (distance / time_diff) * 1.94384  # m/s to knots
                
                # Check for impossible jump
                if distance > self.thresholds['position_jump'] and time_diff < 10:
                    confidence = min(1.0, distance / 5000)
                    
                    alert = SpoofingAlert(
                        alert_id=f"gps_spoof_{uuid.uuid4().hex[:8]}",
                        spoofing_type=SpoofingType.GPS_SPOOFING,
                        confidence=confidence,
                        description=f"GPS position jumped {distance:.0f}m in {time_diff:.1f}s "
                                   f"(implies {implied_speed:.0f} knots)",
                        affected_sensors=['gps'],
                        evidence={
                            'distance_jumped': distance,
                            'time_elapsed': time_diff,
                            'implied_speed': implied_speed,
                            'previous_position': {'lat': prev_lat, 'lon': prev_lon},
                            'current_position': {'lat': current_lat, 'lon': current_lon}
                        },
                        detected_at=datetime.now(),
                        recommended_action="Use AIS and RADAR for navigation. "
                                         "Verify GPS receiver integrity. "
                                         "Report to maritime authorities."
                    )
                    alerts.append(alert)
                
                # Check for impossible speed
                elif implied_speed > self.thresholds['speed_impossibility']:
                    confidence = min(1.0, implied_speed / 100.0)
                    
                    alert = SpoofingAlert(
                        alert_id=f"gps_speed_{uuid.uuid4().hex[:8]}",
                        spoofing_type=SpoofingType.GPS_SPOOFING,
                        confidence=confidence,
                        description=f"GPS shows impossible speed: {implied_speed:.0f} knots",
                        affected_sensors=['gps'],
                        evidence={
                            'implied_speed': implied_speed,
                            'distance': distance,
                            'time_elapsed': time_diff
                        },
                        detected_at=datetime.now(),
                        recommended_action="GPS likely compromised. Use alternative navigation."
                    )
                    alerts.append(alert)
        
        # Update tracking
        self.previous_gps_position = (current_lat, current_lon)
        self.last_update_time = current_time
        
        return alerts
    
    def _detect_ais_spoofing(self, raw_sensor_data: Dict[str, Any]) -> List[Any]:
        """Detect AIS spoofing through inconsistencies"""
        from models.data_models import SpoofingAlert, SpoofingType
        
        alerts = []
        
        if 'ais' not in raw_sensor_data or not raw_sensor_data['ais']:
            return alerts
        
        ais = raw_sensor_data['ais']
        
        # Check for impossible AIS data
        if 'speed' in ais and ais['speed'] > self.thresholds['speed_impossibility']:
            confidence = min(1.0, ais['speed'] / 100.0)
            
            alert = SpoofingAlert(
                alert_id=f"ais_spoof_{uuid.uuid4().hex[:8]}",
                spoofing_type=SpoofingType.AIS_SPOOFING,
                confidence=confidence,
                description=f"AIS reports impossible speed: {ais['speed']:.0f} knots",
                affected_sensors=['ais'],
                evidence={
                    'reported_speed': ais['speed'],
                    'reported_course': ais.get('course'),
                    'mmsi': ais.get('mmsi')
                },
                detected_at=datetime.now(),
                recommended_action="AIS data may be spoofed. Verify with radar and visual."
            )
            alerts.append(alert)
        
        # Check for position jump in AIS
        if 'latitude' in ais and 'longitude' in ais:
            current_lat = ais['latitude']
            current_lon = ais['longitude']
            
            if self.previous_ais_position:
                prev_lat, prev_lon = self.previous_ais_position
                
                distance = self._haversine_distance(
                    prev_lat, prev_lon, current_lat, current_lon
                )
                
                # Large jump in AIS position
                if distance > self.thresholds['position_jump']:
                    confidence = min(1.0, distance / 5000)
                    
                    alert = SpoofingAlert(
                        alert_id=f"ais_jump_{uuid.uuid4().hex[:8]}",
                        spoofing_type=SpoofingType.AIS_SPOOFING,
                        confidence=confidence,
                        description=f"AIS position jumped {distance:.0f}m",
                        affected_sensors=['ais'],
                        evidence={
                            'distance_jumped': distance,
                            'previous_position': {'lat': prev_lat, 'lon': prev_lon},
                            'current_position': {'lat': current_lat, 'lon': current_lon}
                        },
                        detected_at=datetime.now(),
                        recommended_action="Possible AIS spoofing or transmitter malfunction."
                    )
                    alerts.append(alert)
            
            self.previous_ais_position = (current_lat, current_lon)
        
        return alerts
    
    def _detect_multi_sensor_spoofing(
        self, 
        raw_sensor_data: Dict[str, Any], 
        fused_data: Any
    ) -> List[Any]:
        """Detect spoofing through multi-sensor cross-validation (most reliable)"""
        from models.data_models import SpoofingAlert, SpoofingType
        
        alerts = []
        
        # Get positions from different sensors
        positions = {}
        
        if 'gps' in raw_sensor_data and raw_sensor_data['gps']:
            gps = raw_sensor_data['gps']
            if 'latitude' in gps and 'longitude' in gps:
                positions['gps'] = (gps['latitude'], gps['longitude'])
        
        if 'ais' in raw_sensor_data and raw_sensor_data['ais']:
            ais = raw_sensor_data['ais']
            if 'latitude' in ais and 'longitude' in ais:
                positions['ais'] = (ais['latitude'], ais['longitude'])
        
        if 'radar' in raw_sensor_data and raw_sensor_data['radar']:
            radar = raw_sensor_data['radar']
            if 'own_ship' in radar:
                own = radar['own_ship']
                if 'latitude' in own and 'longitude' in own:
                    positions['radar'] = (own['latitude'], own['longitude'])
        
        # Cross-validate all sensors
        if len(positions) >= 2:
            max_mismatch = 0
            mismatch_pairs = []
            
            sensors = list(positions.keys())
            for i in range(len(sensors)):
                for j in range(i + 1, len(sensors)):
                    sensor1, sensor2 = sensors[i], sensors[j]
                    pos1, pos2 = positions[sensor1], positions[sensor2]
                    
                    distance = self._haversine_distance(
                        pos1[0], pos1[1], pos2[0], pos2[1]
                    )
                    
                    if distance > max_mismatch:
                        max_mismatch = distance
                    
                    if distance > self.thresholds['multi_sensor_mismatch']:
                        mismatch_pairs.append({
                            'sensors': [sensor1, sensor2],
                            'distance': distance
                        })
            
            # If multiple sensors disagree significantly, likely spoofing
            if mismatch_pairs:
                # Calculate confidence based on mismatch severity
                confidence = min(1.0, max_mismatch / 2000)
                
                # Determine which sensor is likely spoofed
                affected = self._identify_spoofed_sensor(positions)
                
                alert = SpoofingAlert(
                    alert_id=f"multi_spoof_{uuid.uuid4().hex[:8]}",
                    spoofing_type=SpoofingType.MULTI_SENSOR_SPOOFING,
                    confidence=confidence,
                    description=f"Multiple sensors show position mismatch up to {max_mismatch:.0f}m. "
                               f"Possible {affected} spoofing.",
                    affected_sensors=list(positions.keys()),
                    evidence={
                        'max_mismatch': max_mismatch,
                        'mismatch_pairs': mismatch_pairs,
                        'positions': {k: {'lat': v[0], 'lon': v[1]} for k, v in positions.items()},
                        'likely_spoofed': affected
                    },
                    detected_at=datetime.now(),
                    recommended_action=f"Cross-validate all sensors. {affected.upper()} may be compromised. "
                                     "Use redundant navigation methods."
                )
                alerts.append(alert)
        
        return alerts
    
    def _identify_spoofed_sensor(self, positions: Dict[str, tuple]) -> str:
        """Identify which sensor is most likely spoofed based on consensus"""
        if len(positions) < 3:
            # Can't determine consensus with less than 3 sensors
            return "GPS"  # Default to GPS as most commonly spoofed
        
        # Calculate pairwise distances
        sensors = list(positions.keys())
        outlier_scores = {sensor: 0 for sensor in sensors}
        
        for i in range(len(sensors)):
            for j in range(i + 1, len(sensors)):
                sensor1, sensor2 = sensors[i], sensors[j]
                pos1, pos2 = positions[sensor1], positions[sensor2]
                
                distance = self._haversine_distance(
                    pos1[0], pos1[1], pos2[0], pos2[1]
                )
                
                # Add to outlier scores if distance is large
                if distance > 500:
                    outlier_scores[sensor1] += distance
                    outlier_scores[sensor2] += distance
        
        # Sensor with highest outlier score is likely spoofed
        if outlier_scores:
            spoofed = max(outlier_scores, key=outlier_scores.get)
            return spoofed
        
        return "unknown"
    
    def _detect_time_manipulation(self, raw_sensor_data: Dict[str, Any]) -> List[Any]:
        """Detect timestamp manipulation"""
        from models.data_models import SpoofingAlert, SpoofingType
        
        alerts = []
        current_time = datetime.now()
        
        # Check GPS timestamp
        if 'gps' in raw_sensor_data and raw_sensor_data['gps']:
            gps = raw_sensor_data['gps']
            if 'timestamp' in gps:
                try:
                    gps_time = datetime.fromisoformat(gps['timestamp'])
                    time_diff = abs((current_time - gps_time).total_seconds())
                    
                    # Suspicious if GPS time is off by more than 60 seconds
                    if time_diff > self.thresholds['time_inconsistency']:
                        confidence = min(1.0, time_diff / 300)
                        
                        alert = SpoofingAlert(
                            alert_id=f"time_spoof_{uuid.uuid4().hex[:8]}",
                            spoofing_type=SpoofingType.GPS_SPOOFING,
                            confidence=confidence,
                            description=f"GPS timestamp differs from system time by {time_diff:.0f}s",
                            affected_sensors=['gps'],
                            evidence={
                                'gps_time': gps['timestamp'],
                                'system_time': current_time.isoformat(),
                                'difference_seconds': time_diff
                            },
                            detected_at=datetime.now(),
                            recommended_action="Check GPS receiver. Possible time manipulation attack."
                        )
                        alerts.append(alert)
                except Exception as e:
                    self.logger.error(f"Error parsing GPS timestamp: {e}")
        
        return alerts
    
    def _log_spoofing_incident(self, alerts: List[Any]):
        """Log spoofing incidents for analysis"""
        incident = {
            'timestamp': datetime.now().isoformat(),
            'alert_count': len(alerts),
            'alert_types': [a.spoofing_type.value for a in alerts],
            'max_confidence': max(a.confidence for a in alerts)
        }
        self.spoofing_incidents.append(incident)
        
        # Keep only recent incidents
        if len(self.spoofing_incidents) > 100:
            self.spoofing_incidents.pop(0)
    
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
    
    def get_spoofing_history(self) -> List[Dict[str, Any]]:
        """Get history of spoofing incidents"""
        return self.spoofing_incidents
