"""
Demo Data Simulator
Generates realistic maritime sensor data for demonstrations and testing
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import time


class MaritimeDataSimulator:
    """
    Simulates realistic maritime sensor data including:
    - Normal operation
    - Collision scenarios
    - Spoofing attacks
    - Sensor anomalies
    """
    
    def __init__(self, start_position: Tuple[float, float] = (51.5074, -0.1278)):
        """
        Initialize simulator.
        
        Args:
            start_position: Starting (latitude, longitude)
        """
        # Vessel state
        self.latitude, self.longitude = start_position
        self.speed = 12.0  # knots
        self.course = 45.0  # degrees
        self.heading = 45.0
        self.rot = 0.0  # rate of turn
        
        # Simulation parameters
        self.time_step = 1.0  # seconds
        self.update_count = 0
        
        # Scenario control
        self.scenario = 'normal'  # 'normal', 'collision', 'spoofing', 'anomaly'
        self.scenario_start_time = None
        
        # Target vessels
        self.targets = self._initialize_targets()
        
        print("Maritime Data Simulator initialized")
        print(f"  Start position: {self.latitude:.4f}°N, {self.longitude:.4f}°E")
        print(f"  Initial speed: {self.speed} knots")
        print(f"  Initial course: {self.course}°")
    
    def _initialize_targets(self) -> List[Dict[str, Any]]:
        """Initialize target vessels around own ship"""
        targets = []
        
        # Target 1: Crossing from port
        targets.append({
            'mmsi': '235012345',
            'name': 'MV ALPHA',
            'latitude': self.latitude + 0.02,
            'longitude': self.longitude - 0.05,
            'speed': 15.0,
            'course': 120.0,
            'vessel_type': 'Cargo'
        })
        
        # Target 2: Overtaking from astern
        targets.append({
            'mmsi': '235067890',
            'name': 'MV BRAVO',
            'latitude': self.latitude - 0.03,
            'longitude': self.longitude - 0.01,
            'speed': 18.0,
            'course': 45.0,
            'vessel_type': 'Tanker'
        })
        
        # Target 3: Head-on
        targets.append({
            'mmsi': '235098765',
            'name': 'MV CHARLIE',
            'latitude': self.latitude + 0.08,
            'longitude': self.longitude + 0.08,
            'speed': 14.0,
            'course': 225.0,
            'vessel_type': 'Container'
        })
        
        return targets
    
    def update_vessel_state(self):
        """Update own vessel state based on current course and speed"""
        # Convert speed to degrees per second (rough approximation)
        # 1 knot ≈ 0.000514 degrees latitude per second
        speed_deg_per_sec = self.speed * 0.000514
        
        # Update position based on course
        self.latitude += speed_deg_per_sec * math.cos(math.radians(self.course)) * self.time_step
        self.longitude += speed_deg_per_sec * math.sin(math.radians(self.course)) * self.time_step / math.cos(math.radians(self.latitude))
        
        # Apply rate of turn
        self.course = (self.course + self.rot * (self.time_step / 60.0)) % 360
        self.heading = self.course + random.uniform(-2, 2)  # Slight variation
        
        # Update targets
        self._update_targets()
        
        self.update_count += 1
    
    def _update_targets(self):
        """Update target vessel positions"""
        for target in self.targets:
            speed_deg_per_sec = target['speed'] * 0.000514
            target['latitude'] += speed_deg_per_sec * math.cos(math.radians(target['course'])) * self.time_step
            target['longitude'] += speed_deg_per_sec * math.sin(math.radians(target['course'])) * self.time_step / math.cos(math.radians(target['latitude']))
    
    def generate_sensor_data(self) -> Dict[str, Any]:
        """Generate complete sensor data package"""
        # Update vessel state
        self.update_vessel_state()
        
        # Base sensor data
        sensor_data = {
            'gps': self._generate_gps_data(),
            'ais': self._generate_ais_data(),
            'radar': self._generate_radar_data(),
            'weather': self._generate_weather_data(),
            'engine': self._generate_engine_data(),
            'tide': self._generate_tide_data(),
            'current': self._generate_current_data()
        }
        
        # Apply scenario modifications
        if self.scenario == 'spoofing':
            sensor_data = self._apply_spoofing_scenario(sensor_data)
        elif self.scenario == 'anomaly':
            sensor_data = self._apply_anomaly_scenario(sensor_data)
        elif self.scenario == 'collision':
            self._apply_collision_scenario()
        
        return sensor_data
    
    def _generate_gps_data(self) -> Dict[str, Any]:
        """Generate GPS data with realistic noise"""
        noise_lat = random.gauss(0, 0.00001)  # ~1m std dev
        noise_lon = random.gauss(0, 0.00001)
        
        return {
            'latitude': self.latitude + noise_lat,
            'longitude': self.longitude + noise_lon,
            'speed': self.speed + random.gauss(0, 0.1),
            'course': self.course + random.gauss(0, 0.5),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_ais_data(self) -> Dict[str, Any]:
        """Generate AIS data"""
        noise_lat = random.gauss(0, 0.00002)  # AIS slightly less accurate
        noise_lon = random.gauss(0, 0.00002)
        
        ais_data = {
            'mmsi': '235123456',
            'latitude': self.latitude + noise_lat,
            'longitude': self.longitude + noise_lon,
            'speed': self.speed + random.gauss(0, 0.3),
            'course': self.course + random.gauss(0, 1.0),
            'heading': self.heading + random.gauss(0, 1.0),
            'rot': self.rot + random.gauss(0, 0.5),
            'timestamp': datetime.now().isoformat(),
            'targets': []
        }
        
        # Add target vessels
        for target in self.targets:
            # Calculate CPA and TCPA (simplified)
            distance, bearing = self._calculate_distance_bearing(
                self.latitude, self.longitude,
                target['latitude'], target['longitude']
            )
            
            cpa, tcpa = self._calculate_cpa_tcpa(target, distance, bearing)
            
            ais_data['targets'].append({
                'mmsi': target['mmsi'],
                'name': target['name'],
                'latitude': target['latitude'] + random.gauss(0, 0.00002),
                'longitude': target['longitude'] + random.gauss(0, 0.00002),
                'speed': target['speed'] + random.gauss(0, 0.3),
                'course': target['course'] + random.gauss(0, 1.0),
                'vessel_type': target['vessel_type'],
                'distance': distance,
                'bearing': bearing,
                'cpa': cpa,
                'tcpa': tcpa
            })
        
        return ais_data
    
    def _generate_radar_data(self) -> Dict[str, Any]:
        """Generate radar data"""
        radar_data = {
            'own_ship': {
                'latitude': self.latitude + random.gauss(0, 0.00005),
                'longitude': self.longitude + random.gauss(0, 0.00005)
            },
            'targets': []
        }
        
        # Add radar targets (slightly different from AIS)
        for target in self.targets:
            distance, bearing = self._calculate_distance_bearing(
                self.latitude, self.longitude,
                target['latitude'], target['longitude']
            )
            
            radar_data['targets'].append({
                'latitude': target['latitude'] + random.gauss(0, 0.0001),
                'longitude': target['longitude'] + random.gauss(0, 0.0001),
                'distance': distance + random.gauss(0, 0.05),
                'bearing': bearing + random.gauss(0, 2.0)
            })
        
        return radar_data
    
    def _generate_weather_data(self) -> Dict[str, Any]:
        """Generate weather data"""
        return {
            'wind_speed': 15.0 + random.gauss(0, 2.0),
            'wind_direction': 270.0 + random.gauss(0, 10.0),
            'temperature': 18.0 + random.gauss(0, 1.0),
            'pressure': 1013.0 + random.gauss(0, 5.0),
            'visibility': 'good'
        }
    
    def _generate_engine_data(self) -> Dict[str, Any]:
        """Generate engine data"""
        return {
            'rpm': 1200 + random.gauss(0, 50),
            'fuel_rate': 85.0 + random.gauss(0, 5.0),
            'temperature': 75.0 + random.gauss(0, 2.0),
            'status': 'normal'
        }
    
    def _generate_tide_data(self) -> Dict[str, Any]:
        """Generate tide data"""
        # Simulate tidal cycle
        tide_height = 2.0 * math.sin(2 * math.pi * self.update_count / 720)  # 12-hour cycle
        
        return {
            'height': tide_height + random.gauss(0, 0.1),
            'type': 'flood' if tide_height > 0 else 'ebb'
        }
    
    def _generate_current_data(self) -> Dict[str, Any]:
        """Generate current data"""
        return {
            'speed': 1.5 + random.gauss(0, 0.3),
            'direction': 180.0 + random.gauss(0, 15.0)
        }
    
    def _apply_spoofing_scenario(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply GPS spoofing scenario"""
        # Introduce large position error in GPS
        sensor_data['gps']['latitude'] += 0.01  # ~1km offset
        sensor_data['gps']['longitude'] += 0.01
        sensor_data['gps']['speed'] = 35.0  # Unrealistic speed
        
        print("⚠️  Simulating GPS SPOOFING attack")
        
        return sensor_data
    
    def _apply_anomaly_scenario(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sensor anomaly scenario"""
        # Introduce sensor mismatch
        sensor_data['ais']['latitude'] += 0.003  # 300m mismatch
        sensor_data['ais']['speed'] = self.speed + 8.0  # Speed anomaly
        
        print("⚠️  Simulating sensor anomaly")
        
        return sensor_data
    
    def _apply_collision_scenario(self):
        """Apply collision risk scenario"""
        # Move target closer
        if self.targets:
            self.targets[0]['latitude'] = self.latitude + 0.01
            self.targets[0]['longitude'] = self.longitude + 0.01
            self.targets[0]['course'] = 270.0  # Converging course
    
    def _calculate_distance_bearing(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> Tuple[float, float]:
        """Calculate distance (nm) and bearing (degrees) between two points"""
        # Haversine distance
        R = 3440.065  # Earth radius in nautical miles
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        # Bearing
        y = math.sin(dlambda) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
        bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
        
        return distance, bearing
    
    def _calculate_cpa_tcpa(
        self, 
        target: Dict[str, Any], 
        distance: float, 
        bearing: float
    ) -> Tuple[float, float]:
        """Calculate CPA and TCPA (simplified)"""
        # Relative velocity
        rel_course = (target['course'] - self.course + 360) % 360
        rel_speed = math.sqrt(
            self.speed**2 + target['speed']**2 - 
            2 * self.speed * target['speed'] * math.cos(math.radians(rel_course))
        )
        
        if rel_speed < 0.1:
            return distance, 999.9
        
        # Simplified CPA/TCPA
        tcpa = distance / (rel_speed / 60.0)  # minutes
        cpa = distance * 0.5 if tcpa < 30 else distance  # Simplified
        
        return max(0.0, cpa), max(0.0, min(999.9, tcpa))
    
    def set_scenario(self, scenario: str):
        """Set simulation scenario"""
        self.scenario = scenario
        self.scenario_start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"Scenario changed to: {scenario.upper()}")
        print(f"{'='*60}\n")
    
    def get_vessel_info(self) -> Dict[str, Any]:
        """Get current vessel information"""
        return {
            'position': {'latitude': self.latitude, 'longitude': self.longitude},
            'speed': self.speed,
            'course': self.course,
            'heading': self.heading,
            'scenario': self.scenario,
            'update_count': self.update_count
        }
