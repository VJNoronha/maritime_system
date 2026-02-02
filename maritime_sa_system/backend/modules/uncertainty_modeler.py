"""
Uncertainty Modeling Module
Estimates uncertainty in measurements and fused state using statistical methods
No ML required - uses error propagation and sensor characteristics
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import math


class UncertaintyModeler:
    """
    Models uncertainty in sensor measurements and fused state estimates.
    Uses statistical error propagation and sensor characteristics.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger('UncertaintyModeler')
        
        # Known sensor uncertainties (standard deviations)
        self.sensor_uncertainties = {
            'gps': {
                'position': 5.0,  # meters
                'speed': 0.1,  # knots
                'course': 2.0  # degrees
            },
            'ais': {
                'position': 10.0,  # meters (depends on GPS)
                'speed': 0.5,  # knots
                'course': 5.0  # degrees
            },
            'radar': {
                'position': 50.0,  # meters
                'bearing': 1.0,  # degrees
                'range': 20.0  # meters
            },
            'weather': {
                'wind_speed': 2.0,  # knots
                'wind_direction': 10.0  # degrees
            },
            'tide': {
                'height': 0.1  # meters
            },
            'current': {
                'speed': 0.5,  # knots
                'direction': 15.0  # degrees
            }
        }
        
        # Confidence levels (for confidence intervals)
        self.confidence_level = 0.95  # 95% confidence
        self.z_score = 1.96  # For 95% confidence
        
        self.logger.info("Uncertainty Modeler initialized")
    
    def calculate(
        self, 
        fused_data: Any, 
        raw_sensor_data: Dict[str, Any],
        anomalies: List[Any]
    ) -> Dict[str, Any]:
        """
        Calculate uncertainties for all state parameters.
        
        Args:
            fused_data: Fused sensor data
            raw_sensor_data: Raw sensor readings
            anomalies: Detected anomalies (increase uncertainty)
        
        Returns:
            Dictionary of Uncertainty objects
        """
        from models.data_models import Uncertainty
        
        uncertainties = {}
        
        # 1. Position uncertainty
        uncertainties['position'] = self._calculate_position_uncertainty(
            fused_data, raw_sensor_data
        )
        
        # 2. Speed uncertainty
        uncertainties['speed'] = self._calculate_speed_uncertainty(
            fused_data, raw_sensor_data
        )
        
        # 3. Course uncertainty
        uncertainties['course'] = self._calculate_course_uncertainty(
            fused_data, raw_sensor_data
        )
        
        # 4. Heading uncertainty
        uncertainties['heading'] = self._calculate_heading_uncertainty(
            fused_data, raw_sensor_data
        )
        
        # 5. Target tracking uncertainty
        uncertainties['targets'] = self._calculate_target_uncertainty(
            fused_data
        )
        
        # 6. Environmental uncertainties
        env_uncertainties = self._calculate_environmental_uncertainty(
            fused_data
        )
        uncertainties.update(env_uncertainties)
        
        # Adjust uncertainties based on anomalies
        if anomalies:
            self._adjust_for_anomalies(uncertainties, anomalies)
        
        self.logger.debug(f"Calculated {len(uncertainties)} uncertainty estimates")
        
        return uncertainties
    
    def _calculate_position_uncertainty(
        self, 
        fused_data: Any, 
        raw_sensor_data: Dict[str, Any]
    ) -> Any:
        """Calculate position uncertainty using error propagation"""
        from models.data_models import Uncertainty
        
        # Collect position measurements with their uncertainties
        measurements = []
        
        if 'gps' in raw_sensor_data and raw_sensor_data['gps']:
            measurements.append(('gps', self.sensor_uncertainties['gps']['position']))
        
        if 'ais' in raw_sensor_data and raw_sensor_data['ais']:
            measurements.append(('ais', self.sensor_uncertainties['ais']['position']))
        
        if 'radar' in raw_sensor_data and raw_sensor_data['radar']:
            measurements.append(('radar', self.sensor_uncertainties['radar']['position']))
        
        # Calculate combined uncertainty using weighted variance
        if not measurements:
            # High uncertainty if no measurements
            std_dev = 100.0
        elif len(measurements) == 1:
            # Single sensor uncertainty
            std_dev = measurements[0][1]
        else:
            # Multiple sensors - reduce uncertainty
            # Use formula: 1/σ² = Σ(1/σᵢ²)
            inv_var_sum = sum(1.0 / (sigma**2) for _, sigma in measurements)
            std_dev = math.sqrt(1.0 / inv_var_sum)
        
        # Calculate 95% confidence interval
        ci_range = self.z_score * std_dev
        mean_value = 0.0  # Relative to fused position
        
        # Reliability based on number of sensors and quality
        reliability = min(1.0, len(measurements) / 3.0) * 0.9  # Max 90% for position
        
        return Uncertainty(
            parameter='position',
            mean_value=mean_value,
            std_deviation=std_dev,
            confidence_interval=(-ci_range, ci_range),
            reliability=reliability
        )
    
    def _calculate_speed_uncertainty(
        self, 
        fused_data: Any, 
        raw_sensor_data: Dict[str, Any]
    ) -> Any:
        """Calculate speed uncertainty"""
        from models.data_models import Uncertainty
        
        measurements = []
        
        if 'gps' in raw_sensor_data and raw_sensor_data['gps']:
            if 'speed' in raw_sensor_data['gps']:
                measurements.append(self.sensor_uncertainties['gps']['speed'])
        
        if 'ais' in raw_sensor_data and raw_sensor_data['ais']:
            if 'speed' in raw_sensor_data['ais']:
                measurements.append(self.sensor_uncertainties['ais']['speed'])
        
        # Calculate combined uncertainty
        if not measurements:
            std_dev = 2.0
            reliability = 0.3
        elif len(measurements) == 1:
            std_dev = measurements[0]
            reliability = 0.7
        else:
            inv_var_sum = sum(1.0 / (sigma**2) for sigma in measurements)
            std_dev = math.sqrt(1.0 / inv_var_sum)
            reliability = 0.9
        
        ci_range = self.z_score * std_dev
        
        return Uncertainty(
            parameter='speed',
            mean_value=fused_data.vessel_state.speed,
            std_deviation=std_dev,
            confidence_interval=(
                fused_data.vessel_state.speed - ci_range,
                fused_data.vessel_state.speed + ci_range
            ),
            reliability=reliability
        )
    
    def _calculate_course_uncertainty(
        self, 
        fused_data: Any, 
        raw_sensor_data: Dict[str, Any]
    ) -> Any:
        """Calculate course uncertainty"""
        from models.data_models import Uncertainty
        
        measurements = []
        
        if 'gps' in raw_sensor_data and raw_sensor_data['gps']:
            if 'course' in raw_sensor_data['gps']:
                measurements.append(self.sensor_uncertainties['gps']['course'])
        
        if 'ais' in raw_sensor_data and raw_sensor_data['ais']:
            if 'course' in raw_sensor_data['ais']:
                measurements.append(self.sensor_uncertainties['ais']['course'])
        
        if not measurements:
            std_dev = 10.0
            reliability = 0.3
        elif len(measurements) == 1:
            std_dev = measurements[0]
            reliability = 0.7
        else:
            inv_var_sum = sum(1.0 / (sigma**2) for sigma in measurements)
            std_dev = math.sqrt(1.0 / inv_var_sum)
            reliability = 0.9
        
        ci_range = self.z_score * std_dev
        course = fused_data.vessel_state.course
        
        return Uncertainty(
            parameter='course',
            mean_value=course,
            std_deviation=std_dev,
            confidence_interval=(
                (course - ci_range) % 360,
                (course + ci_range) % 360
            ),
            reliability=reliability
        )
    
    def _calculate_heading_uncertainty(
        self, 
        fused_data: Any, 
        raw_sensor_data: Dict[str, Any]
    ) -> Any:
        """Calculate heading uncertainty"""
        from models.data_models import Uncertainty
        
        # Heading typically comes from compass/gyro via AIS
        if 'ais' in raw_sensor_data and raw_sensor_data['ais']:
            if 'heading' in raw_sensor_data['ais']:
                std_dev = 5.0  # Compass uncertainty
                reliability = 0.8
            else:
                std_dev = 10.0
                reliability = 0.5
        else:
            std_dev = 15.0
            reliability = 0.3
        
        ci_range = self.z_score * std_dev
        heading = fused_data.vessel_state.heading
        
        return Uncertainty(
            parameter='heading',
            mean_value=heading,
            std_deviation=std_dev,
            confidence_interval=(
                (heading - ci_range) % 360,
                (heading + ci_range) % 360
            ),
            reliability=reliability
        )
    
    def _calculate_target_uncertainty(self, fused_data: Any) -> Any:
        """Calculate uncertainty in target tracking"""
        from models.data_models import Uncertainty
        
        if not fused_data.targets:
            return Uncertainty(
                parameter='targets',
                mean_value=0.0,
                std_deviation=0.0,
                confidence_interval=(0.0, 0.0),
                reliability=1.0
            )
        
        # Average CPA/TCPA uncertainty across targets
        avg_cpa_uncertainty = 0.5  # nautical miles
        avg_tcpa_uncertainty = 2.0  # minutes
        
        # Calculate overall target tracking reliability
        reliability = 0.7 if len(fused_data.targets) > 0 else 0.0
        
        return Uncertainty(
            parameter='targets',
            mean_value=len(fused_data.targets),
            std_deviation=math.sqrt(len(fused_data.targets)),
            confidence_interval=(
                max(0, len(fused_data.targets) - 2),
                len(fused_data.targets) + 2
            ),
            reliability=reliability
        )
    
    def _calculate_environmental_uncertainty(self, fused_data: Any) -> Dict[str, Any]:
        """Calculate environmental parameter uncertainties"""
        from models.data_models import Uncertainty
        
        uncertainties = {}
        
        # Wind uncertainty
        uncertainties['wind'] = Uncertainty(
            parameter='wind',
            mean_value=0.0,
            std_deviation=self.sensor_uncertainties['weather']['wind_speed'],
            confidence_interval=(-4.0, 4.0),
            reliability=0.7
        )
        
        # Current uncertainty
        uncertainties['current'] = Uncertainty(
            parameter='current',
            mean_value=0.0,
            std_deviation=self.sensor_uncertainties['current']['speed'],
            confidence_interval=(-1.0, 1.0),
            reliability=0.6
        )
        
        # Tide uncertainty
        uncertainties['tide'] = Uncertainty(
            parameter='tide',
            mean_value=0.0,
            std_deviation=self.sensor_uncertainties['tide']['height'],
            confidence_interval=(-0.2, 0.2),
            reliability=0.8
        )
        
        return uncertainties
    
    def _adjust_for_anomalies(
        self, 
        uncertainties: Dict[str, Any], 
        anomalies: List[Any]
    ):
        """Adjust uncertainties based on detected anomalies"""
        if not anomalies:
            return
        
        # Calculate anomaly impact factor
        max_severity = max(a.severity for a in anomalies)
        impact_factor = 1.0 + max_severity  # Increase uncertainty by up to 2x
        
        # Increase uncertainties for affected parameters
        for anomaly in anomalies:
            if 'position' in str(anomaly.anomaly_type.value):
                if 'position' in uncertainties:
                    unc = uncertainties['position']
                    unc.std_deviation *= impact_factor
                    unc.reliability *= (1.0 - anomaly.severity * 0.3)
            
            if 'speed' in str(anomaly.anomaly_type.value):
                if 'speed' in uncertainties:
                    unc = uncertainties['speed']
                    unc.std_deviation *= impact_factor
                    unc.reliability *= (1.0 - anomaly.severity * 0.3)
            
            if 'sensor' in str(anomaly.anomaly_type.value):
                # Reduce reliability for all measurements
                for unc in uncertainties.values():
                    unc.reliability *= (1.0 - anomaly.severity * 0.2)
        
        self.logger.debug(f"Adjusted uncertainties for {len(anomalies)} anomalies")
    
    def estimate_collision_uncertainty(
        self, 
        target_distance: float, 
        target_speed: float, 
        own_speed: float
    ) -> Tuple[float, float]:
        """
        Estimate uncertainty in collision prediction.
        
        Returns:
            (cpa_uncertainty, tcpa_uncertainty) in nautical miles and minutes
        """
        # CPA uncertainty increases with distance and speed
        cpa_uncertainty = 0.1 + (target_distance * 0.02)
        
        # TCPA uncertainty depends on speeds
        combined_speed = target_speed + own_speed
        tcpa_uncertainty = 1.0 if combined_speed > 0 else 5.0
        tcpa_uncertainty += target_distance * 0.5
        
        return cpa_uncertainty, tcpa_uncertainty
