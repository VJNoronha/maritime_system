"""
Sensor Fusion Module
Combines data from multiple sensors using weighted averaging and Kalman-style filtering
No ML required - uses algorithmic sensor fusion techniques
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import math


class SensorFusionEngine:
    """
    Fuses multi-sensor data using weighted averaging based on sensor reliability.
    Implements temporal smoothing and outlier rejection.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger('SensorFusion')
        
        # Sensor reliability weights
        self.sensor_weights = {
            'gps': 0.95,
            'ais': 0.85,
            'radar': 0.80,
            'chart': 0.90,
            'weather': 0.75,
            'engine': 0.85,
            'camera': 0.70,
            'tide': 0.80,
            'current': 0.75
        }
        
        # State history for smoothing
        self.position_history: List[Tuple[float, float, datetime]] = []
        self.max_history = 50
        
        # Outlier detection thresholds
        self.position_outlier_threshold = 0.001  # ~100 meters
        self.speed_outlier_threshold = 10.0  # knots
        
        self.logger.info("Sensor Fusion Engine initialized")
    
    def fuse(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fuse multi-sensor data into unified state.
        
        Args:
            sensor_data: Dictionary with sensor readings
        
        Returns:
            Fused data dictionary
        """
        from models.data_models import FusedData, VesselState, Position, Target
        
        timestamp = datetime.now()
        
        # Fuse vessel state
        vessel_state = self._fuse_vessel_state(sensor_data)
        
        # Fuse targets
        targets = self._fuse_targets(sensor_data)
        
        # Fuse environment
        environment = self._fuse_environment(sensor_data)
        
        # Calculate quality scores
        quality_scores = self._calculate_quality_scores(sensor_data)
        
        # Calculate fusion confidence
        fusion_confidence = self._calculate_fusion_confidence(quality_scores)
        
        fused_data = FusedData(
            vessel_state=vessel_state,
            targets=targets,
            environment=environment,
            quality_scores=quality_scores,
            fusion_confidence=fusion_confidence,
            timestamp=timestamp
        )
        
        self.logger.debug(f"Fused {len(sensor_data)} sensors, confidence: {fusion_confidence:.2f}")
        
        return fused_data
    
    def _fuse_vessel_state(self, sensor_data: Dict[str, Any]) -> Any:
        """Fuse vessel state from multiple sensors"""
        from models.data_models import VesselState, Position
        
        # Collect position estimates
        positions = []
        speeds = []
        courses = []
        headings = []
        rots = []
        
        # GPS data (highest priority)
        if 'gps' in sensor_data and sensor_data['gps']:
            gps = sensor_data['gps']
            weight = self.sensor_weights['gps']
            
            if 'latitude' in gps and 'longitude' in gps:
                if not self._is_position_outlier(gps['latitude'], gps['longitude']):
                    positions.append((gps['latitude'], gps['longitude'], weight))
            
            if 'speed' in gps and not self._is_speed_outlier(gps['speed']):
                speeds.append((gps['speed'], weight))
            
            if 'course' in gps:
                courses.append((gps['course'], weight))
        
        # AIS data
        if 'ais' in sensor_data and sensor_data['ais']:
            ais = sensor_data['ais']
            weight = self.sensor_weights['ais']
            
            if 'latitude' in ais and 'longitude' in ais:
                if not self._is_position_outlier(ais['latitude'], ais['longitude']):
                    positions.append((ais['latitude'], ais['longitude'], weight))
            
            if 'speed' in ais and not self._is_speed_outlier(ais['speed']):
                speeds.append((ais['speed'], weight))
            
            if 'course' in ais:
                courses.append((ais['course'], weight))
            
            if 'heading' in ais:
                headings.append((ais['heading'], weight))
            
            if 'rot' in ais:
                rots.append((ais['rot'], weight))
        
        # Radar data (backup)
        if 'radar' in sensor_data and sensor_data['radar']:
            radar = sensor_data['radar']
            if 'own_ship' in radar:
                own = radar['own_ship']
                weight = self.sensor_weights['radar'] * 0.8
                
                if 'latitude' in own and 'longitude' in own:
                    if not self._is_position_outlier(own['latitude'], own['longitude']):
                        positions.append((own['latitude'], own['longitude'], weight))
        
        # Perform weighted fusion
        fused_lat, fused_lon = self._weighted_position_fusion(positions)
        fused_speed = self._weighted_value_fusion(speeds, default=0.0)
        fused_course = self._weighted_angle_fusion(courses, default=0.0)
        fused_heading = self._weighted_angle_fusion(headings, default=fused_course)
        fused_rot = self._weighted_value_fusion(rots, default=0.0)
        
        # Update history
        self._update_position_history(fused_lat, fused_lon)
        
        return VesselState(
            position=Position(latitude=fused_lat, longitude=fused_lon),
            speed=fused_speed,
            course=fused_course,
            heading=fused_heading,
            rate_of_turn=fused_rot,
            timestamp=datetime.now()
        )
    
    def _weighted_position_fusion(
        self, 
        positions: List[Tuple[float, float, float]]
    ) -> Tuple[float, float]:
        """Fuse position estimates with weights"""
        if not positions:
            return 0.0, 0.0
        
        total_weight = sum(w for _, _, w in positions)
        lat = sum(lat * w for lat, _, w in positions) / total_weight
        lon = sum(lon * w for _, lon, w in positions) / total_weight
        
        return lat, lon
    
    def _weighted_value_fusion(
        self, 
        values: List[Tuple[float, float]], 
        default: float = 0.0
    ) -> float:
        """Fuse scalar values with weights"""
        if not values:
            return default
        
        total_weight = sum(w for _, w in values)
        return sum(v * w for v, w in values) / total_weight
    
    def _weighted_angle_fusion(
        self, 
        angles: List[Tuple[float, float]], 
        default: float = 0.0
    ) -> float:
        """Fuse angles (0-360) properly handling wraparound"""
        if not angles:
            return default
        
        # Convert to unit vectors
        sin_sum = sum(math.sin(math.radians(a)) * w for a, w in angles)
        cos_sum = sum(math.cos(math.radians(a)) * w for a, w in angles)
        
        # Calculate weighted circular mean
        angle = math.degrees(math.atan2(sin_sum, cos_sum))
        
        # Normalize to [0, 360)
        return angle % 360
    
    def _is_position_outlier(self, lat: float, lon: float) -> bool:
        """Check if position is an outlier compared to history"""
        if not self.position_history:
            return False
        
        # Get most recent position
        last_lat, last_lon, last_time = self.position_history[-1]
        
        # Calculate distance
        distance = self._haversine_distance(lat, lon, last_lat, last_lon)
        
        # Check if distance is unreasonable
        time_diff = (datetime.now() - last_time).total_seconds()
        if time_diff > 0:
            # Max reasonable speed: 50 knots = 25.7 m/s
            max_distance = 25.7 * time_diff
            return distance > max_distance * 2  # 2x safety factor
        
        return False
    
    def _is_speed_outlier(self, speed: float) -> bool:
        """Check if speed is unreasonable"""
        # Most commercial vessels: 0-30 knots
        # Allow up to 50 knots for high-speed vessels
        return speed < 0 or speed > 50
    
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
    
    def _update_position_history(self, lat: float, lon: float):
        """Update position history for temporal smoothing"""
        self.position_history.append((lat, lon, datetime.now()))
        
        # Keep only recent history
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)
    
    def _fuse_targets(self, sensor_data: Dict[str, Any]) -> List[Any]:
        """Fuse target tracking data from AIS and radar"""
        from models.data_models import Target, Position
        
        targets = []
        target_dict = {}
        
        # Get AIS targets
        if 'ais' in sensor_data and 'targets' in sensor_data['ais']:
            for ais_target in sensor_data['ais']['targets']:
                target_id = ais_target.get('mmsi', f"ais_{len(targets)}")
                target_dict[target_id] = {
                    'source': 'ais',
                    'data': ais_target,
                    'weight': self.sensor_weights['ais']
                }
        
        # Get radar targets
        if 'radar' in sensor_data and 'targets' in sensor_data['radar']:
            for radar_target in sensor_data['radar']['targets']:
                # Try to correlate with AIS
                target_id = self._correlate_target(radar_target, target_dict)
                
                if target_id:
                    # Merge with existing
                    target_dict[target_id]['radar_data'] = radar_target
                else:
                    # New radar-only target
                    target_id = f"radar_{len(target_dict)}"
                    target_dict[target_id] = {
                        'source': 'radar',
                        'data': radar_target,
                        'weight': self.sensor_weights['radar']
                    }
        
        # Create Target objects
        for target_id, target_info in target_dict.items():
            try:
                data = target_info['data']
                
                target = Target(
                    target_id=target_id,
                    position=Position(
                        latitude=data.get('latitude', 0.0),
                        longitude=data.get('longitude', 0.0)
                    ),
                    speed=data.get('speed', 0.0),
                    course=data.get('course', 0.0),
                    cpa=data.get('cpa', 999.9),
                    tcpa=data.get('tcpa', 999.9),
                    distance=data.get('distance', 999.9),
                    vessel_type=data.get('vessel_type'),
                    name=data.get('name')
                )
                targets.append(target)
            except Exception as e:
                self.logger.error(f"Error creating target {target_id}: {e}")
        
        return targets
    
    def _correlate_target(
        self, 
        radar_target: Dict[str, Any], 
        existing_targets: Dict[str, Any]
    ) -> Optional[str]:
        """Correlate radar target with existing AIS targets"""
        # Simple distance-based correlation
        radar_lat = radar_target.get('latitude')
        radar_lon = radar_target.get('longitude')
        
        if radar_lat is None or radar_lon is None:
            return None
        
        correlation_threshold = 500  # meters
        
        for target_id, target_info in existing_targets.items():
            if target_info['source'] != 'ais':
                continue
            
            ais_data = target_info['data']
            ais_lat = ais_data.get('latitude')
            ais_lon = ais_data.get('longitude')
            
            if ais_lat is not None and ais_lon is not None:
                distance = self._haversine_distance(
                    radar_lat, radar_lon, ais_lat, ais_lon
                )
                
                if distance < correlation_threshold:
                    return target_id
        
        return None
    
    def _fuse_environment(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fuse environmental data"""
        environment = {
            'weather': {},
            'tide': {},
            'current': {},
            'visibility': 'good'
        }
        
        if 'weather' in sensor_data and sensor_data['weather']:
            environment['weather'] = sensor_data['weather']
        
        if 'tide' in sensor_data and sensor_data['tide']:
            environment['tide'] = sensor_data['tide']
        
        if 'current' in sensor_data and sensor_data['current']:
            environment['current'] = sensor_data['current']
        
        return environment
    
    def _calculate_quality_scores(self, sensor_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality score for each sensor"""
        quality_scores = {}
        
        for sensor_key in sensor_data:
            if sensor_data[sensor_key] is not None:
                # Simple quality based on data completeness
                data = sensor_data[sensor_key]
                if isinstance(data, dict):
                    # More fields = higher quality
                    quality = min(1.0, len(data) / 10.0)
                else:
                    quality = 0.5
                
                quality_scores[sensor_key] = quality
        
        return quality_scores
    
    def _calculate_fusion_confidence(self, quality_scores: Dict[str, float]) -> float:
        """Calculate overall fusion confidence"""
        if not quality_scores:
            return 0.0
        
        # Weighted average of quality scores
        total_weight = 0
        weighted_sum = 0
        
        for sensor, quality in quality_scores.items():
            weight = self.sensor_weights.get(sensor, 0.5)
            weighted_sum += quality * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
