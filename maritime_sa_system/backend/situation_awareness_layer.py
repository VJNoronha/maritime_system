"""
Situation Awareness Layer - Main Orchestrator
Maritime Navigation Decision Support System

Coordinates all awareness modules to provide comprehensive situational awareness
with real-time monitoring, alerting, and data fusion.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from models.data_models import (
    SituationAwarenessOutput, Alert, AlertLevel
)
from modules.sensor_fusion import SensorFusionEngine
from modules.anomaly_detector import AnomalyDetector
from modules.spoofing_detector import SpoofingDetector
from modules.uncertainty_modeler import UncertaintyModeler


class SituationAwarenessLayer:
    """
    Main orchestrator for the Situation Awareness Layer.
    
    Coordinates sensor fusion, anomaly detection, spoofing detection,
    and uncertainty modeling to provide comprehensive maritime situational awareness.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Situation Awareness Layer.
        
        Args:
            config: Configuration dictionary for all modules
        """
        self.config = config or {}
        self.logger = self._setup_logging()
        
        # Initialize all modules
        self.logger.info("Initializing Situation Awareness Layer modules...")
        
        self.sensor_fusion = SensorFusionEngine(
            config=self.config.get('sensor_fusion', {})
        )
        
        self.anomaly_detector = AnomalyDetector(
            config=self.config.get('anomaly_detection', {})
        )
        
        self.spoofing_detector = SpoofingDetector(
            config=self.config.get('spoofing_detection', {})
        )
        
        self.uncertainty_modeler = UncertaintyModeler(
            config=self.config.get('uncertainty', {})
        )
        
        # System status tracking
        self.system_status = {
            'sensor_fusion': 'operational',
            'anomaly_detection': 'operational',
            'spoofing_detection': 'operational',
            'uncertainty_modeling': 'operational'
        }
        
        # Performance metrics
        self.processing_times: List[float] = []
        self.max_processing_time_history = 100
        
        self.logger.info("✓ Situation Awareness Layer initialized successfully")
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the layer"""
        logger = logging.getLogger('SituationAwareness')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
        
        return logger
    
    def process_sensor_data(self, sensor_data: Dict[str, Any]) -> SituationAwarenessOutput:
        """
        Process incoming sensor data through all awareness modules.
        
        This is the main entry point for processing sensor data.
        
        Args:
            sensor_data: Dictionary containing data from all sensors
                {
                    'ais': {...},
                    'radar': {...},
                    'gps': {...},
                    'weather': {...},
                    'engine': {...},
                    'cameras': {...},
                    'charts': {...},
                    'tides': {...},
                    'currents': {...}
                }
        
        Returns:
            SituationAwarenessOutput with complete assessment
        """
        start_time = datetime.now()
        
        try:
            self.logger.debug("=" * 60)
            self.logger.debug("Processing new sensor data batch")
            
            # Step 1: Fuse sensor data
            self.logger.debug("→ Running sensor fusion...")
            fused_data = self.sensor_fusion.fuse(sensor_data)
            self.logger.debug(f"  Fusion confidence: {fused_data.fusion_confidence:.2f}")
            
            # Step 2: Detect spoofing (high priority)
            self.logger.debug("→ Checking for spoofing...")
            spoofing_alerts = self.spoofing_detector.detect(sensor_data, fused_data)
            if spoofing_alerts:
                self.logger.warning(f"  ⚠️  {len(spoofing_alerts)} SPOOFING ALERT(S) DETECTED!")
            
            # Step 3: Detect anomalies
            self.logger.debug("→ Running anomaly detection...")
            anomalies = self.anomaly_detector.detect(fused_data, sensor_data)
            if anomalies:
                self.logger.debug(f"  Found {len(anomalies)} anomalies")
            
            # Step 4: Model uncertainties
            self.logger.debug("→ Modeling uncertainties...")
            uncertainties = self.uncertainty_modeler.calculate(
                fused_data, sensor_data, anomalies
            )
            
            # Step 5: Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                fused_data, uncertainties, anomalies, spoofing_alerts
            )
            self.logger.debug(f"  Overall confidence: {overall_confidence:.2f}")
            
            # Step 6: Generate consolidated alerts
            alerts = self._generate_alerts(
                spoofing_alerts, anomalies, uncertainties, overall_confidence
            )
            
            if alerts:
                self.logger.info(f"Generated {len(alerts)} alerts")
                for alert in alerts:
                    if alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                        self.logger.warning(f"  [{alert.level.value.upper()}] {alert.title}")
            
            # Create output
            output = SituationAwarenessOutput(
                timestamp=datetime.now(),
                fused_data=fused_data,
                anomalies=anomalies,
                uncertainties=uncertainties,
                spoofing_alerts=spoofing_alerts,
                overall_confidence=overall_confidence,
                alerts=alerts,
                system_status=self.system_status.copy()
            )
            
            # Track processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(processing_time)
            
            self.logger.debug(f"Processing completed in {processing_time:.3f}s")
            self.logger.debug("=" * 60)
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error processing sensor data: {e}", exc_info=True)
            self._handle_processing_error(e)
            raise
    
    def _calculate_overall_confidence(
        self,
        fused_data: Any,
        uncertainties: Dict[str, Any],
        anomalies: List[Any],
        spoofing_alerts: List[Any]
    ) -> float:
        """
        Calculate overall confidence in situational awareness.
        
        Factors:
        - Fusion confidence from sensor fusion
        - Number and severity of anomalies
        - Presence of spoofing
        - Uncertainty levels
        """
        # Start with fusion confidence
        confidence = fused_data.fusion_confidence
        
        # Reduce confidence for anomalies
        if anomalies:
            max_severity = max(a.severity for a in anomalies)
            avg_severity = sum(a.severity for a in anomalies) / len(anomalies)
            anomaly_penalty = (max_severity * 0.3 + avg_severity * 0.2) * 0.5
            confidence *= (1.0 - anomaly_penalty)
        
        # Significant penalty for spoofing
        if spoofing_alerts:
            max_spoof_confidence = max(s.confidence for s in spoofing_alerts)
            spoofing_penalty = max_spoof_confidence * 0.5
            confidence *= (1.0 - spoofing_penalty)
        
        # Factor in uncertainty reliability
        if uncertainties:
            avg_reliability = sum(
                u.reliability for u in uncertainties.values()
            ) / len(uncertainties)
            confidence = (confidence + avg_reliability) / 2
        
        # Ensure confidence stays in [0, 1]
        return max(0.0, min(1.0, confidence))
    
    def _generate_alerts(
        self,
        spoofing_alerts: List[Any],
        anomalies: List[Any],
        uncertainties: Dict[str, Any],
        overall_confidence: float
    ) -> List[Alert]:
        """Generate consolidated alert list from all sources"""
        alerts = []
        
        # Convert spoofing alerts (highest priority)
        for spoof_alert in spoofing_alerts:
            alert = Alert(
                alert_id=spoof_alert.alert_id,
                level=spoof_alert.to_alert_level(),
                title=f"🚨 SPOOFING DETECTED: {spoof_alert.spoofing_type.value.replace('_', ' ').upper()}",
                message=spoof_alert.description + "\n\n" + spoof_alert.recommended_action,
                timestamp=spoof_alert.detected_at,
                source='spoofing_detector',
                metadata={
                    'spoofing_type': spoof_alert.spoofing_type.value,
                    'confidence': spoof_alert.confidence,
                    'evidence': spoof_alert.evidence,
                    'affected_sensors': spoof_alert.affected_sensors
                }
            )
            alerts.append(alert)
        
        # Convert anomalies to alerts
        for anomaly in anomalies:
            alert = Alert(
                alert_id=anomaly.anomaly_id,
                level=anomaly.to_alert_level(),
                title=f"{anomaly.anomaly_type.value.replace('_', ' ').title()}",
                message=anomaly.description,
                timestamp=anomaly.detected_at,
                source='anomaly_detector',
                metadata={
                    'anomaly_type': anomaly.anomaly_type.value,
                    'severity': anomaly.severity,
                    'affected_sensors': anomaly.affected_sensors,
                    'location': anomaly.location.to_dict() if anomaly.location else None
                }
            )
            alerts.append(alert)
        
        # Alert for low overall confidence
        if overall_confidence < 0.5:
            alert = Alert(
                alert_id=f"low_conf_{uuid.uuid4().hex[:8]}",
                level=AlertLevel.WARNING,
                title="Low Situational Awareness Confidence",
                message=f"Overall confidence is {overall_confidence:.1%}. "
                       "Exercise caution and verify sensor readings.",
                timestamp=datetime.now(),
                source='situation_awareness',
                metadata={'overall_confidence': overall_confidence}
            )
            alerts.append(alert)
        
        # Sort by priority (use key function instead of comparison)
        level_priority = {
            AlertLevel.EMERGENCY: 4,
            AlertLevel.CRITICAL: 3,
            AlertLevel.WARNING: 2,
            AlertLevel.INFO: 1
        }
        alerts.sort(key=lambda a: level_priority.get(a.level, 0), reverse=True)
        
        return alerts
    
    def _update_metrics(self, processing_time: float):
        """Update performance metrics"""
        self.processing_times.append(processing_time)
        
        # Keep only recent history
        if len(self.processing_times) > self.max_processing_time_history:
            self.processing_times.pop(0)
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get system performance metrics"""
        if not self.processing_times:
            return {
                'avg_processing_time': 0.0,
                'max_processing_time': 0.0,
                'min_processing_time': 0.0
            }
        
        return {
            'avg_processing_time': sum(self.processing_times) / len(self.processing_times),
            'max_processing_time': max(self.processing_times),
            'min_processing_time': min(self.processing_times),
            'samples': len(self.processing_times)
        }
    
    def _handle_processing_error(self, error: Exception):
        """Handle processing errors and update system status"""
        self.logger.error(f"Processing error: {error}")
        
        # Update system status to degraded
        for module in self.system_status:
            self.system_status[module] = 'degraded'
    
    def get_system_status(self) -> Dict[str, str]:
        """Get current system status"""
        return self.system_status.copy()
    
    def reset(self):
        """Reset the layer (clear history)"""
        self.logger.info("Resetting Situation Awareness Layer")
        
        # Reinitialize modules to clear history
        self.sensor_fusion = SensorFusionEngine(
            config=self.config.get('sensor_fusion', {})
        )
        self.anomaly_detector = AnomalyDetector(
            config=self.config.get('anomaly_detection', {})
        )
        self.spoofing_detector = SpoofingDetector(
            config=self.config.get('spoofing_detection', {})
        )
        self.uncertainty_modeler = UncertaintyModeler(
            config=self.config.get('uncertainty', {})
        )
        
        # Reset metrics
        self.processing_times.clear()
        
        for module in self.system_status:
            self.system_status[module] = 'operational'
        
        self.logger.info("Reset complete")


if __name__ == "__main__":
    # Quick test
    print("Situation Awareness Layer - Production Ready")
    print("=" * 60)
    
    sa_layer = SituationAwarenessLayer()
    
    # Test with sample data
    test_data = {
        'gps': {
            'latitude': 51.5074,
            'longitude': -0.1278,
            'speed': 12.5,
            'course': 45.0
        },
        'ais': {
            'latitude': 51.5074,
            'longitude': -0.1278,
            'speed': 12.3,
            'course': 45.5,
            'heading': 46.0,
            'rot': 2.0
        }
    }
    
    output = sa_layer.process_sensor_data(test_data)
    print(f"\nProcessing result:")
    print(f"  Confidence: {output.overall_confidence:.2%}")
    print(f"  Anomalies: {len(output.anomalies)}")
    print(f"  Spoofing: {len(output.spoofing_alerts)}")
    print(f"  Alerts: {len(output.alerts)}")
    
    metrics = sa_layer.get_performance_metrics()
    print(f"\nPerformance:")
    print(f"  Processing time: {metrics['avg_processing_time']:.3f}s")
