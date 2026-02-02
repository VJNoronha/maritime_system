# Maritime Video Analysis System
## Upload Videos & Apply SA Layer Analysis

A simple, working dashboard that allows you to upload maritime video footage and apply all Situation Awareness Layer features in real-time.

---

## 🎯 What This Does

Upload any maritime video and the system will:
1. **Extract vessel movements** from the video
2. **Generate sensor data** (GPS, AIS, RADAR-like data)
3. **Run through SA Layer** with all 4 modules:
   - Sensor Fusion
   - Anomaly Detection
   - Spoofing Detection
   - Uncertainty Modeling
4. **Display results in real-time** as the video plays

---

## 🚀 Quick Start

### Linux/Mac:
```bash
chmod +x start_video_analysis.sh
./start_video_analysis.sh
```

### Windows:
```batch
start_video_analysis.bat
```

### Manual:
```bash
pip install -r requirements.txt
cd backend
python video_server.py
```

Then open: **http://localhost:5000**

---

## 📹 How to Use

1. **Start the server** (see Quick Start above)
2. **Open browser** to http://localhost:5000
3. **Upload a video**
   - Click the upload zone or drag & drop
   - Supports: MP4, AVI, MOV, MKV, WebM
   - Max size: 500MB
4. **Click "Start Analysis"**
   - Watch as the video processes frame-by-frame
   - See real-time SA layer output
   - View alerts, anomalies, and statistics
5. **Control playback**
   - Stop: Pause processing
   - Reset: Go back to beginning

---

## 📊 What You'll See

### Real-Time Dashboard Displays:

**Video Playback**
- Current frame displayed
- Progress bar showing position in video
- Frame counter

**SA Layer Statistics**
- Overall Confidence (0-100%)
- Anomalies Detected
- Spoofing Alerts
- Active Alerts

**Vessel State**
- Speed (knots)
- Course (degrees)
- Position (lat/lon)
- Number of targets detected

**Active Alerts**
- Real-time alerts as they occur
- Color-coded by severity:
  - 🔴 Emergency (red)
  - 🟠 Critical (orange)
  - 🟡 Warning (yellow)
  - 🔵 Info (blue)

---

## 🎬 Video Processing Pipeline

```
Video Upload
    ↓
Frame-by-Frame Processing
    ↓
Object Detection (vessels, movement)
    ↓
Synthetic Sensor Data Generation
    ↓
SA Layer Processing
    │
    ├─→ Sensor Fusion
    ├─→ Spoofing Detection
    ├─→ Anomaly Detection
    └─→ Uncertainty Modeling
    ↓
Real-Time Dashboard Updates
```

---

## 🔧 Technical Details

### Video Processing
- **Method**: OpenCV-based frame analysis
- **Detection**: Background subtraction + contour detection
- **Rate**: ~10 frames per second processing
- **Data Generated**: GPS, AIS, RADAR, Weather, Engine, Tide, Current

### SA Layer Integration
- All 4 modules run on every frame
- Real-time anomaly detection
- Spoofing checks on synthetic sensor data
- Uncertainty modeling for all measurements

### Dashboard
- **Update Rate**: 5 Hz (200ms refresh)
- **Technology**: HTML + Vanilla JavaScript
- **API**: RESTful endpoints
- **Streaming**: Base64-encoded JPEG frames

---

## 📁 New Files

```
maritime_sa_system/
├── backend/
│   ├── video_processor.py         # NEW: Video processing module
│   ├── video_server.py             # NEW: Flask server for video
│   └── [existing SA layer files]
│
├── dashboard/
│   └── video_dashboard.html        # NEW: Video analysis UI
│
├── start_video_analysis.sh         # NEW: Quick start (Linux/Mac)
├── start_video_analysis.bat        # NEW: Quick start (Windows)
└── requirements.txt                # UPDATED: Added OpenCV
```

---

## 🎨 Dashboard Features

### Upload Section
- Drag & drop support
- Click to browse
- File type validation
- Upload progress

### Video Display
- Current frame preview
- Frame counter overlay
- Progress bar
- Smooth playback

### Controls
- ▶ Start Analysis
- ⏸ Stop (pause)
- ↻ Reset (go to beginning)

### Real-Time Data
- Confidence meter
- Statistics grid
- Alert feed
- Vessel state

---

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload video file |
| `/api/start_processing` | POST | Start analyzing video |
| `/api/stop_processing` | POST | Stop processing |
| `/api/reset` | POST | Reset to beginning |
| `/api/status` | GET | Get SA layer output |
| `/api/frame` | GET | Get current frame (base64) |

---

## 🎯 Use Cases

1. **Maritime Training**
   - Analyze recorded navigation scenarios
   - Identify anomalies in historical footage
   - Study vessel behavior patterns

2. **Incident Investigation**
   - Process dashcam or surveillance footage
   - Detect anomalies leading to incidents
   - Generate reports with SA layer data

3. **System Validation**
   - Test SA layer with real video data
   - Validate detection algorithms
   - Benchmark performance

4. **Research & Development**
   - Video-based sensor simulation
   - Algorithm testing with visual data
   - Comparison studies

---

## 🔍 What Gets Detected

### From Video Analysis:
- **Moving objects** (potential vessels)
- **Object positions** (pixel → lat/lon conversion)
- **Movement patterns** (speed, direction estimation)
- **Relative distances** (based on object size)

### Generated Sensor Data:
- **GPS**: Own ship position, speed, course
- **AIS**: Own ship + detected targets with CPA/TCPA
- **RADAR**: Target positions and bearings
- **Weather**: Synthetic (static)
- **Engine**: Synthetic (based on speed)
- **Tide/Current**: Synthetic (static)

### SA Layer Detections:
- **Anomalies**: Trajectory deviations, speed changes, etc.
- **Spoofing**: Cross-sensor validation failures
- **Uncertainties**: Measurement confidence levels
- **Alerts**: Prioritized notifications

---

## ⚙️ Configuration

### Video Processing
- Object detection sensitivity (in `video_processor.py`)
- Frame processing rate (in `video_server.py`)
- Minimum object size threshold

### SA Layer
- All original thresholds apply
- Anomaly detection rules
- Spoofing detection criteria
- Uncertainty parameters

---

## 🐛 Troubleshooting

### Video won't upload
- Check file size (max 500MB)
- Verify format (MP4, AVI, MOV, MKV, WebM)
- Check disk space in /tmp

### Processing is slow
- Large videos take time
- Reduce video resolution before upload
- Close other applications

### No objects detected
- Video may not have moving objects
- Adjust detection sensitivity
- Ensure video has maritime content

### Dashboard not updating
- Check browser console for errors
- Verify server is running
- Refresh the page

---

## 📊 Performance

- **Upload Speed**: Depends on connection
- **Processing Rate**: ~10 fps
- **Dashboard Updates**: 5 Hz
- **Memory Usage**: ~100-200MB (depends on video)
- **Supported Video Length**: Up to 10 minutes recommended

---

## 🔒 Security Notes

- Videos stored in `/tmp` (temporary)
- No authentication (demo only)
- Run on localhost only
- For production, add authentication & HTTPS

---

## 🎓 How It Works

### 1. Video Upload
- File validation
- Secure storage
- OpenCV loading

### 2. Frame Processing
- Background subtraction removes static elements
- Morphological operations clean noise
- Contour detection finds moving objects
- Bounding boxes track targets

### 3. Data Generation
- Pixel coordinates → geographic positions
- Object size → distance estimation
- Movement tracking → speed/course
- Synthetic sensor data creation

### 4. SA Layer Analysis
- Sensor fusion combines all data
- Anomaly detection checks patterns
- Spoofing detection validates consistency
- Uncertainty modeling calculates confidence

### 5. Dashboard Display
- JSON API returns SA output
- Frame streaming via base64
- Real-time statistics
- Alert notifications

---

## 📈 Future Enhancements

Potential improvements:
- [ ] Live camera feed support
- [ ] Advanced object detection (YOLO/SSD)
- [ ] Vessel classification
- [ ] Trajectory prediction
- [ ] Historical data storage
- [ ] Video export with overlays
- [ ] Multi-video comparison

---

## 🎉 Ready to Use!

The system is fully functional and ready for video analysis.

**Try it with any maritime video footage!**

Need sample videos? Search for:
- "maritime navigation video"
- "ship bridge view"
- "vessel traffic video"
- "harbor surveillance"

---

## 📞 Support

All code is documented and commented.
Check the browser console and server logs for debugging.

**Happy Analyzing! 🚢📹**
