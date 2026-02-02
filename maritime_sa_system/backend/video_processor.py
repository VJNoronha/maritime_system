"""
Video Processing Module
Extracts maritime sensor-like data from video footage for SA Layer analysis
"""

import cv2
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging


class MaritimeVideoProcessor:
    """
    Processes maritime video footage and extracts sensor-like data.
    Simulates GPS, AIS, and RADAR data from visual analysis.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('VideoProcessor')
        self.logger.setLevel(logging.INFO)
        
        # Video properties
        self.video_path = None
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.current_frame = 0
        
        # Vessel tracking
        self.own_ship_position = (0.0, 0.0)  # Simulated lat/lon
        self.own_ship_speed = 12.0  # knots
        self.own_ship_course = 45.0  # degrees
        
        # Object detection (simple motion-based)
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
        
        # Tracked targets
        self.targets = {}
        self.target_id_counter = 0
        
        self.logger.info("Maritime Video Processor initialized")
    
    def load_video(self, video_path: str) -> bool:
        """
        Load a video file for processing.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.video_path = video_path
            self.cap = cv2.VideoCapture(video_path)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open video: {video_path}")
                return False
            
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_frame = 0
            
            self.logger.info(f"Loaded video: {video_path}")
            self.logger.info(f"  FPS: {self.fps}")
            self.logger.info(f"  Total frames: {self.frame_count}")
            self.logger.info(f"  Duration: {self.frame_count/self.fps:.1f}s")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading video: {e}")
            return False
    
    def process_frame(self) -> Optional[Dict[str, Any]]:
        """
        Process the next frame and extract sensor data.
        
        Returns:
            Dictionary with simulated sensor data, or None if video ended
        """
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            self.logger.info("End of video reached")
            return None
        
        self.current_frame += 1
        
        # Process frame to detect objects
        detected_objects = self._detect_objects(frame)
        
        # Update vessel state based on motion
        self._update_vessel_state(frame)
        
        # Generate sensor data
        sensor_data = self._generate_sensor_data(detected_objects)
        
        # Add frame metadata
        sensor_data['video_metadata'] = {
            'current_frame': self.current_frame,
            'total_frames': self.frame_count,
            'timestamp': datetime.now().isoformat(),
            'progress': (self.current_frame / self.frame_count) * 100
        }
        
        return sensor_data
    
    def _detect_objects(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect moving objects in the frame (potential vessels).
        Uses background subtraction and contour detection.
        """
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)
        
        # Noise removal
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(
            fg_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        detected_objects = []
        
        # Filter and track significant objects
        min_area = 500  # Minimum object area to consider
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area > min_area:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate center
                center_x = x + w // 2
                center_y = y + h // 2
                
                detected_objects.append({
                    'center': (center_x, center_y),
                    'bbox': (x, y, w, h),
                    'area': area
                })
        
        return detected_objects
    
    def _update_vessel_state(self, frame: np.ndarray):
        """
        Update own ship state based on video analysis.
        Simulates vessel movement through the scene.
        """
        # Simulate movement (advance position slightly each frame)
        # In real implementation, this could use optical flow or other techniques
        speed_change = np.random.normal(0, 0.1)
        course_change = np.random.normal(0, 0.5)
        
        self.own_ship_speed = max(0, self.own_ship_speed + speed_change)
        self.own_ship_course = (self.own_ship_course + course_change) % 360
        
        # Update position (simplified - real would use actual vessel tracking)
        # Move in the direction of course
        speed_deg_per_frame = self.own_ship_speed * 0.00001
        
        lat_change = speed_deg_per_frame * np.cos(np.radians(self.own_ship_course))
        lon_change = speed_deg_per_frame * np.sin(np.radians(self.own_ship_course))
        
        new_lat = self.own_ship_position[0] + lat_change
        new_lon = self.own_ship_position[1] + lon_change
        
        self.own_ship_position = (new_lat, new_lon)
    
    def _generate_sensor_data(self, detected_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate simulated sensor data from detected objects.
        Creates GPS, AIS, and RADAR-like data.
        """
        # GPS data (own ship)
        gps_data = {
            'latitude': 51.5074 + self.own_ship_position[0],
            'longitude': -0.1278 + self.own_ship_position[1],
            'speed': self.own_ship_speed + np.random.normal(0, 0.1),
            'course': self.own_ship_course + np.random.normal(0, 1.0),
            'timestamp': datetime.now().isoformat()
        }
        
        # AIS data (own ship + detected targets)
        ais_targets = []
        
        for i, obj in enumerate(detected_objects[:5]):  # Limit to 5 targets
            # Convert pixel position to relative bearing/distance
            frame_center = (640, 360)  # Assume 1280x720 video
            dx = obj['center'][0] - frame_center[0]
            dy = obj['center'][1] - frame_center[1]
            
            # Calculate relative bearing
            bearing = np.degrees(np.arctan2(dx, -dy)) % 360
            
            # Estimate distance based on object size (very rough)
            # Larger objects are closer
            distance = max(1.0, 10.0 - (obj['area'] / 1000.0))
            
            # Calculate target position relative to own ship
            target_lat = gps_data['latitude'] + (distance * 0.001 * np.cos(np.radians(bearing)))
            target_lon = gps_data['longitude'] + (distance * 0.001 * np.sin(np.radians(bearing)))
            
            # Estimate target speed and course (simplified)
            target_speed = np.random.uniform(8, 18)
            target_course = (bearing + np.random.uniform(-30, 30)) % 360
            
            # Calculate CPA and TCPA (simplified)
            cpa = distance * np.random.uniform(0.5, 0.9)
            tcpa = np.random.uniform(5, 20)
            
            ais_targets.append({
                'mmsi': f'23501{1000 + i}',
                'name': f'TARGET_{i+1}',
                'latitude': target_lat,
                'longitude': target_lon,
                'speed': target_speed,
                'course': target_course,
                'vessel_type': 'Unknown',
                'distance': distance,
                'bearing': bearing,
                'cpa': cpa,
                'tcpa': tcpa
            })
        
        ais_data = {
            'mmsi': '235123456',
            'latitude': gps_data['latitude'] + np.random.normal(0, 0.00002),
            'longitude': gps_data['longitude'] + np.random.normal(0, 0.00002),
            'speed': gps_data['speed'] + np.random.normal(0, 0.3),
            'course': gps_data['course'] + np.random.normal(0, 1.0),
            'heading': gps_data['course'] + np.random.normal(0, 2.0),
            'rot': np.random.normal(0, 1.0),
            'timestamp': datetime.now().isoformat(),
            'targets': ais_targets
        }
        
        # RADAR data
        radar_targets = []
        for i, obj in enumerate(detected_objects[:5]):
            frame_center = (640, 360)
            dx = obj['center'][0] - frame_center[0]
            dy = obj['center'][1] - frame_center[1]
            
            bearing = np.degrees(np.arctan2(dx, -dy)) % 360
            distance = max(1.0, 10.0 - (obj['area'] / 1000.0))
            
            target_lat = gps_data['latitude'] + (distance * 0.001 * np.cos(np.radians(bearing)))
            target_lon = gps_data['longitude'] + (distance * 0.001 * np.sin(np.radians(bearing)))
            
            radar_targets.append({
                'latitude': target_lat + np.random.normal(0, 0.0001),
                'longitude': target_lon + np.random.normal(0, 0.0001),
                'distance': distance + np.random.normal(0, 0.05),
                'bearing': bearing + np.random.normal(0, 2.0)
            })
        
        radar_data = {
            'own_ship': {
                'latitude': gps_data['latitude'] + np.random.normal(0, 0.00005),
                'longitude': gps_data['longitude'] + np.random.normal(0, 0.00005)
            },
            'targets': radar_targets
        }
        
        # Weather data (static for video)
        weather_data = {
            'wind_speed': 15.0 + np.random.normal(0, 2.0),
            'wind_direction': 270.0 + np.random.normal(0, 10.0),
            'temperature': 18.0 + np.random.normal(0, 1.0),
            'pressure': 1013.0 + np.random.normal(0, 5.0),
            'visibility': 'good'
        }
        
        # Engine data
        engine_data = {
            'rpm': 1200 + np.random.normal(0, 50),
            'fuel_rate': 85.0 + np.random.normal(0, 5.0),
            'temperature': 75.0 + np.random.normal(0, 2.0),
            'status': 'normal'
        }
        
        # Tide and current (static)
        tide_data = {
            'height': 2.0 + np.random.normal(0, 0.1),
            'type': 'flood'
        }
        
        current_data = {
            'speed': 1.5 + np.random.normal(0, 0.3),
            'direction': 180.0 + np.random.normal(0, 15.0)
        }
        
        return {
            'gps': gps_data,
            'ais': ais_data,
            'radar': radar_data,
            'weather': weather_data,
            'engine': engine_data,
            'tide': tide_data,
            'current': current_data
        }
    
    def get_progress(self) -> float:
        """Get current progress through video (0.0 to 1.0)"""
        if self.frame_count == 0:
            return 0.0
        return self.current_frame / self.frame_count
    
    def get_current_frame_image(self) -> Optional[np.ndarray]:
        """Get the current frame as an image"""
        if self.cap is None:
            return None
        
        # Go back one frame to get current
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame - 1)
        ret, frame = self.cap.read()
        
        return frame if ret else None
    
    def reset(self):
        """Reset video to beginning"""
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0
            self.own_ship_position = (0.0, 0.0)
            self.targets = {}
    
    def release(self):
        """Release video resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
