"""
Demo API Server
Flask-based API for the Situation Awareness Layer demo
Serves real-time data to the dashboard
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import sys
from pathlib import Path
import time
import threading
import json

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from situation_awareness_layer import SituationAwarenessLayer
from demo_simulator import MaritimeDataSimulator

# Initialize Flask app
app = Flask(__name__, static_folder='../dashboard')
CORS(app)  # Enable CORS for frontend

# Initialize SA Layer and Simulator
sa_layer = SituationAwarenessLayer()
simulator = MaritimeDataSimulator()

# Store latest output
latest_output = None
output_lock = threading.Lock()


def background_processing():
    """Background thread for continuous processing"""
    global latest_output
    
    while True:
        try:
            # Generate sensor data
            sensor_data = simulator.generate_sensor_data()
            
            # Process through SA layer
            output = sa_layer.process_sensor_data(sensor_data)
            
            # Store output
            with output_lock:
                latest_output = output
            
            # Sleep for update interval
            time.sleep(1.0)  # 1 Hz updates
            
        except Exception as e:
            print(f"Error in background processing: {e}")
            time.sleep(1.0)


# Start background thread
processing_thread = threading.Thread(target=background_processing, daemon=True)
processing_thread.start()


@app.route('/')
def index():
    """Serve the dashboard"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/status')
def get_status():
    """Get current SA layer output"""
    with output_lock:
        if latest_output is None:
            return jsonify({'status': 'initializing'})
        
        try:
            return jsonify(latest_output.to_dict())
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/vessel')
def get_vessel_info():
    """Get current vessel information"""
    return jsonify(simulator.get_vessel_info())


@app.route('/api/metrics')
def get_metrics():
    """Get performance metrics"""
    metrics = sa_layer.get_performance_metrics()
    return jsonify(metrics)


@app.route('/api/system')
def get_system_status():
    """Get system status"""
    return jsonify(sa_layer.get_system_status())


@app.route('/api/scenario/<scenario_name>', methods=['POST'])
def set_scenario(scenario_name):
    """Change simulation scenario"""
    valid_scenarios = ['normal', 'collision', 'spoofing', 'anomaly']
    
    if scenario_name not in valid_scenarios:
        return jsonify({'error': 'Invalid scenario'}), 400
    
    simulator.set_scenario(scenario_name)
    return jsonify({'status': 'success', 'scenario': scenario_name})


@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Reset the SA layer"""
    sa_layer.reset()
    return jsonify({'status': 'reset complete'})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Maritime Situation Awareness Layer - Demo Server")
    print("="*60)
    print("\nAPI Endpoints:")
    print("  GET  /api/status    - Get SA layer output")
    print("  GET  /api/vessel    - Get vessel info")
    print("  GET  /api/metrics   - Get performance metrics")
    print("  GET  /api/system    - Get system status")
    print("  POST /api/scenario/<name> - Change scenario")
    print("  POST /api/reset     - Reset system")
    print("\nScenarios: normal, collision, spoofing, anomaly")
    print("\nStarting server on http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
