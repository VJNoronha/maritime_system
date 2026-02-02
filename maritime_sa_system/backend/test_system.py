"""
System Test Script
Verifies all modules are working correctly
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from situation_awareness_layer import SituationAwarenessLayer
from demo_simulator import MaritimeDataSimulator


def test_system():
    """Run comprehensive system test"""
    print("\n" + "="*60)
    print("Maritime Situation Awareness Layer - System Test")
    print("="*60 + "\n")
    
    # Test 1: Initialize SA Layer
    print("Test 1: Initializing SA Layer...")
    try:
        sa_layer = SituationAwarenessLayer()
        print("✓ SA Layer initialized successfully")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 2: Initialize Simulator
    print("\nTest 2: Initializing Simulator...")
    try:
        simulator = MaritimeDataSimulator()
        print("✓ Simulator initialized successfully")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 3: Normal scenario
    print("\nTest 3: Testing Normal Scenario...")
    try:
        sensor_data = simulator.generate_sensor_data()
        output = sa_layer.process_sensor_data(sensor_data)
        print(f"✓ Processed successfully")
        print(f"  - Confidence: {output.overall_confidence:.2%}")
        print(f"  - Anomalies: {len(output.anomalies)}")
        print(f"  - Spoofing: {len(output.spoofing_alerts)}")
        print(f"  - Alerts: {len(output.alerts)}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 4: Spoofing scenario
    print("\nTest 4: Testing Spoofing Detection...")
    try:
        simulator.set_scenario('spoofing')
        sensor_data = simulator.generate_sensor_data()
        output = sa_layer.process_sensor_data(sensor_data)
        print(f"✓ Spoofing scenario processed")
        print(f"  - Spoofing alerts: {len(output.spoofing_alerts)}")
        if output.spoofing_alerts:
            print(f"  - Detection confidence: {output.spoofing_alerts[0].confidence:.2%}")
            print("  ✓ Spoofing detected successfully!")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 5: Performance metrics
    print("\nTest 5: Checking Performance Metrics...")
    try:
        metrics = sa_layer.get_performance_metrics()
        print(f"✓ Metrics retrieved")
        print(f"  - Avg processing time: {metrics['avg_processing_time']:.3f}s")
        print(f"  - Max processing time: {metrics['max_processing_time']:.3f}s")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 6: JSON serialization
    print("\nTest 6: Testing Data Serialization...")
    try:
        json_output = output.to_json()
        print(f"✓ JSON serialization successful")
        print(f"  - JSON length: {len(json_output)} characters")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60 + "\n")
    
    return True


def test_modules():
    """Test individual modules"""
    print("\n" + "="*60)
    print("Module-Level Tests")
    print("="*60 + "\n")
    
    # Test imports
    print("Testing module imports...")
    try:
        from modules.sensor_fusion import SensorFusionEngine
        from modules.anomaly_detector import AnomalyDetector
        from modules.spoofing_detector import SpoofingDetector
        from modules.uncertainty_modeler import UncertaintyModeler
        import models.data_models
        print("✓ All modules imported successfully")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    
    # Test individual module initialization
    print("\nTesting individual module initialization...")
    try:
        fusion = SensorFusionEngine()
        anomaly = AnomalyDetector()
        spoofing = SpoofingDetector()
        uncertainty = UncertaintyModeler()
        print("✓ All modules initialized successfully")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False
    
    print("\n✓ Module tests passed!\n")
    return True


if __name__ == "__main__":
    print("\n🚢 Maritime Situation Awareness Layer - System Verification")
    
    # Run module tests
    if not test_modules():
        print("\n✗ Module tests failed!")
        sys.exit(1)
    
    # Run system tests
    if not test_system():
        print("\n✗ System tests failed!")
        sys.exit(1)
    
    print("\n🎉 System is ready for demo!")
    print("\nNext steps:")
    print("  1. Run: python demo_server.py")
    print("  2. Open: http://localhost:5000")
    print("  3. Watch: Real-time situational awareness in action!\n")
