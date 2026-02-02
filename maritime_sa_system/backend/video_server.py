"""
Video Analysis Server
Flask API for uploading and analyzing maritime videos with SA Layer
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
from pathlib import Path
import threading
import time
import base64

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from situation_awareness_layer import SituationAwarenessLayer
from video_processor import MaritimeVideoProcessor

# Initialize Flask app
app = Flask(__name__, static_folder='../dashboard')
CORS(app)

# Configuration
UPLOAD_FOLDER = '/tmp/maritime_uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize SA Layer and Video Processor
sa_layer = SituationAwarenessLayer()
video_processor = MaritimeVideoProcessor()

# Processing state
processing_state = {
    'is_processing': False,
    'video_loaded': False,
    'current_output': None,
    'progress': 0.0,
    'video_path': None
}
processing_lock = threading.Lock()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the video analysis dashboard"""
    return send_from_directory(app.static_folder, 'video_dashboard.html')


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Handle video file upload"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Load video
        with processing_lock:
            if video_processor.load_video(filepath):
                processing_state['video_loaded'] = True
                processing_state['video_path'] = filepath
                processing_state['progress'] = 0.0
                
                return jsonify({
                    'status': 'success',
                    'message': 'Video uploaded and loaded successfully',
                    'filename': filename,
                    'frame_count': video_processor.frame_count,
                    'fps': video_processor.fps,
                    'duration': video_processor.frame_count / video_processor.fps if video_processor.fps > 0 else 0
                })
            else:
                return jsonify({'error': 'Failed to load video'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/start_processing', methods=['POST'])
def start_processing():
    """Start processing the loaded video"""
    with processing_lock:
        if not processing_state['video_loaded']:
            return jsonify({'error': 'No video loaded'}), 400
        
        if processing_state['is_processing']:
            return jsonify({'error': 'Already processing'}), 400
        
        processing_state['is_processing'] = True
    
    # Start processing in background thread
    thread = threading.Thread(target=process_video_loop, daemon=True)
    thread.start()
    
    return jsonify({
        'status': 'success',
        'message': 'Video processing started'
    })


@app.route('/api/stop_processing', methods=['POST'])
def stop_processing():
    """Stop video processing"""
    with processing_lock:
        processing_state['is_processing'] = False
    
    return jsonify({
        'status': 'success',
        'message': 'Video processing stopped'
    })


@app.route('/api/reset', methods=['POST'])
def reset_video():
    """Reset video to beginning"""
    with processing_lock:
        processing_state['is_processing'] = False
        if processing_state['video_loaded']:
            video_processor.reset()
            processing_state['progress'] = 0.0
    
    return jsonify({
        'status': 'success',
        'message': 'Video reset to beginning'
    })


@app.route('/api/status')
def get_status():
    """Get current processing status and SA output"""
    with processing_lock:
        if processing_state['current_output'] is None:
            return jsonify({
                'video_loaded': processing_state['video_loaded'],
                'is_processing': processing_state['is_processing'],
                'progress': processing_state['progress'],
                'status': 'no_data'
            })
        
        try:
            # Convert SA output to dict
            output_dict = processing_state['current_output'].to_dict()
            output_dict['video_loaded'] = processing_state['video_loaded']
            output_dict['is_processing'] = processing_state['is_processing']
            output_dict['progress'] = processing_state['progress']
            
            return jsonify(output_dict)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/frame')
def get_current_frame():
    """Get current video frame as base64 image"""
    try:
        frame = video_processor.get_current_frame_image()
        
        if frame is None:
            return jsonify({'error': 'No frame available'}), 404
        
        # Resize for web display
        import cv2
        frame = cv2.resize(frame, (640, 360))
        
        # Convert to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        
        # Convert to base64
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'frame': f'data:image/jpeg;base64,{frame_base64}',
            'progress': processing_state['progress']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def process_video_loop():
    """Background loop to process video frames"""
    print("Starting video processing loop...")
    
    while True:
        with processing_lock:
            if not processing_state['is_processing']:
                break
        
        try:
            # Process next frame
            sensor_data = video_processor.process_frame()
            
            if sensor_data is None:
                # End of video
                print("End of video reached")
                with processing_lock:
                    processing_state['is_processing'] = False
                break
            
            # Process through SA layer
            sa_output = sa_layer.process_sensor_data(sensor_data)
            
            # Update state
            with processing_lock:
                processing_state['current_output'] = sa_output
                processing_state['progress'] = video_processor.get_progress()
            
            # Control processing speed (process at ~10 fps)
            time.sleep(0.1)
        
        except Exception as e:
            print(f"Error in processing loop: {e}")
            with processing_lock:
                processing_state['is_processing'] = False
            break
    
    print("Video processing loop ended")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Maritime Video Analysis System")
    print("="*60)
    print("\nAPI Endpoints:")
    print("  POST /api/upload           - Upload video file")
    print("  POST /api/start_processing - Start analyzing video")
    print("  POST /api/stop_processing  - Stop processing")
    print("  POST /api/reset            - Reset to beginning")
    print("  GET  /api/status           - Get SA layer output")
    print("  GET  /api/frame            - Get current frame")
    print("\nSupported formats: mp4, avi, mov, mkv, webm")
    print("Max file size: 500MB")
    print("\nStarting server on http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
