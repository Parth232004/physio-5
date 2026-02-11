# PhysioSafe VR Safety System - User Guide

## Quick Start

### 1. Install Dependencies
```bash
cd physio-5
pip install -r requirements.txt
```

### 2. Run with Webcam
```bash
python main.py --camera 0 --format json
```

---

## What Happens After Camera Opens

### Step 1: System Initialization (5-10 seconds)
```
PhysioSafe VR Safety System - Neuro-Safe Engine
============================================================
Version: 2.0.0
Mode: Webcam Tracking
Output Format: json
Cooldown: Enabled
Deduplication: Enabled
============================================================
✓ System initialized successfully
```

**Wait for this message before positioning the patient.**

### Step 2: Position the Patient

**Camera View Requirements:**
- Patient should face the camera directly
- Upper body (shoulders to wrists) must be visible
- Good lighting on the patient's face and upper body
- Patient should sit/stand 3-6 feet from camera
- Background should be relatively clean (no clutter)

**Patient Setup:**
1. Ask patient to sit/stand comfortably
2. Ensure their shoulders and arms are visible
3. Patient should be able to move arms freely
4. Explain: "This system will monitor your exercise safety"

### Step 3: System Starts Tracking

Once initialized, the system begins real-time monitoring:

```
Starting safety monitoring...
------------------------------------------------------------
```

---

## Understanding the Output

### Safe Position (Green output)
```
[Frame 1] ✓ SAFE
  Confidence: 87.5%
  Severity: 0/3
  Phase: rest
  FPS: 30.0
```

**Action:** Patient can begin exercises.

### Warning Position (Yellow output)
```
[Frame 45] ⚠ WARNING
  Confidence: 85.2%
  Severity: 2/3
  Phase: active
  Violations: 1
  Correction: Reduce shoulder flexion angle
```

**Action:** Therapist should observe. Patient may need adjustment.

### Danger Position (Red output - FAIL-SAFE)
```
╔═══════════════════════════════════════════════════════════════╗
║  ⚠️  ⚠️  ⚠️  FAIL-SAFE ACTIVATED  ⚠️  ⚠️  ⚠️                ║
╠═══════════════════════════════════════════════════════════════╣
║  FRAME: 157  |  TIME: 5.234s                                ║
║  SAFETY: DANGER  |  SEVERITY: 3 (CRITICAL)                 ║
║  CONFIDENCE: 95%  |  ACTIVE VIOLATIONS: 1                 ║
║                                                               ║
║  PRIMARY VIOLATION: shoulder_left flexion                     ║
║  CURRENT ANGLE: 135.0°  |  SAFE LIMIT: 120°                 ║
║                                                               ║
║  ⚠️  STOP EXERCISE IMMEDIATELY  ⚠️                           ║
╚═══════════════════════════════════════════════════════════════╝
```

**Action:** Immediately stop exercise. Check patient safety.

---

## Output Format Guide

### JSON Output (Default)
```json
{
  "frame": 157,
  "safety_flag": "warning",
  "confidence": 0.87,
  "severity": 2,
  "phase": "active",
  "correction": {
    "joint": "shoulder_left",
    "direction": "lower",
    "target_angle": 120.0,
    "instruction": "Reduce shoulder flexion angle"
  }
}
```

### VR Output (For VR Integration)
```json
{
  "safety": {"status": "warning", "is_safe": true},
  "confidence": {"value": 0.87, "severity": 2},
  "haptic": {"intensity": 150, "duration_ms": 200}
}
```

---

## Confidence Score Meaning

| Score | Meaning | Action |
|-------|---------|--------|
| ≥90% | Very High | Full reliance on system |
| 75-89% | High | Standard monitoring |
| 60-74% | Moderate | Increased attention |
| 45-59% | Low | Visual verification |
| <45% | Very Low | Manual monitoring |

**If confidence is low:**
- Check lighting
- Reposition patient
- Ensure full upper body visible

---

## Phase Detection

The system automatically detects exercise phases:

| Phase | Description |
|-------|-------------|
| rest | Arms at sides, no movement |
| initiation | Beginning of movement |
| active | Full exercise movement |
| transition | Between movements |
| completion | Returning to rest |

---

## Common Issues & Solutions

### Issue: Camera Not Opening
```bash
# Check camera index
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"

# Try different camera index
python main.py --camera 1
```

### Issue: Low Confidence (<60%)
1. Improve lighting on patient
2. Reposition patient closer to camera
3. Remove clutter from background
4. Ask patient to face camera directly

### Issue: No Pose Detection
1. Ensure patient is in camera view
2. Check MediaPipe installation: `pip install mediapipe`
3. Restart the application

### Issue: False Warnings
1. Calibrate patient-specific thresholds
2. Run calibration: `python calibration_workflow.py`
3. Adjust config.json thresholds

---

## Running a Session

### Quick Test (60 seconds, mock mode)
```bash
python run_demo.py --quick-test
```

### Full Session (5 minutes, webcam)
```bash
python run_demo.py --duration 300 --webcam
```

### With Logging
```bash
python run_demo.py --duration 900 --webcam
```
- Creates log files in `logs/` directory
- Records all safety signals
- Exports session for analysis

---

## Stopping the System

**Safe Shutdown:**
1. Press `Ctrl+C` in terminal
2. System performs graceful shutdown
3. Statistics displayed:
```
Session Summary
------------------------------------------------------------
Total Frames: 1578
Duration: 52.6 seconds
Average FPS: 30.0
Safe signals: 1456
Warning signals: 98
Danger signals: 24
Suppressed signals: 45
✓ System shutdown complete
```

---

## Calibration (For Personalized Thresholds)

Create patient-specific safety limits:

```bash
python calibration_workflow.py
```

This guides you through:
1. Patient information entry
2. Mobility level assessment
3. Range of motion measurement
4. Safety limit setting
5. Validation

---

## Keyboard Controls

| Key | Action |
|-----|--------|
| `Ctrl+C` | Emergency stop + graceful shutdown |
| `Ctrl+Z` | Suspend (resume with `fg`) |

---

## Safety Reminders

⚠️ **Important:**
- System is a safety AID, not a replacement for therapist
- Always have qualified therapist present
- Patient should report any pain immediately
- Verify system accuracy before critical exercises
- Low confidence scores require increased vigilance

---

## For Developers

### Run Tests
```bash
python test_system.py
```

### Add New Exercises
Edit `config.json` with new joint/movement thresholds.

### Integrate with VR
Use `vr_signal_adapter.py` for VR-specific output formats.

---

## Troubleshooting Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Camera working (`python main.py --camera 0`)
- [ ] Good lighting on patient
- [ ] Patient positioned correctly
- [ ] Confidence score ≥60%
- [ ] Safety thresholds calibrated for patient
- [ ] Therapist monitoring throughout
