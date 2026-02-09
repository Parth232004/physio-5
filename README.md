# PhysioSafe VR Safety System

**Version: 2.0.0** | **Date: 7 Feb 2025**

A deterministic, neuro-safe real-time signal engine for physiotherapy exercises that works with VR technology.

---

## What Works

### ✅ Completed Deliverables

1. **Medical Grounding Layer** (`medical_constraints.py`)
   - Safe/caution/stop ranges per joint + phase
   - Rule-based, configurable thresholds
   - Deterministic medical validation

2. **Neuro-Safe Signal Engine** (`signal_generator.py`)
   - Per-frame JSON signals with phase, severity, correction, confidence, safety_flag
   - Cooldowns and de-duplication
   - Zero spam, zero ambiguity

3. **VR/Unreal Adapter Contract** (`vr_signal_adapter.py`)
   - Engine-agnostic signal schema
   - Python-side adapters for VR and Unreal
   - Example payloads for Unreal consumption

4. **Demo Hardening + Submission** (`run_demo.py`)
   - 10-15 minute continuous run capability
   - Timestamped logs of signals + safety events
   - Session export for analysis

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Quick 60-second test (mock mode)
python run_demo.py --quick-test

# 15-minute demo with webcam
python run_demo.py --duration 900

# Run tests
python test_system.py
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PhysioSafe System                          │
├─────────────────────────────────────────────────────────────────┤
│  Webcam Input                                                  │
│       ↓                                                        │
│  Pose Tracker (MediaPipe)                                      │
│       ↓                                                        │
│  Angle Calculator                                             │
│       ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Medical Grounding Layer                                 │  │
│  │ • Safe/Caution/Stop thresholds per joint + phase        │  │
│  │ • Deterministic validation                              │  │
│  └─────────────────────────────────────────────────────────┘  │
│       ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Neuro-Safe Signal Engine                                │  │
│  │ • Per-frame JSON signals                                │  │
│  │ • Phase, severity, correction, confidence, safety_flag  │  │
│  │ • Cooldowns + de-duplication                            │  │
│  └─────────────────────────────────────────────────────────┘  │
│       ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ VR/Unreal Adapter                                       │  │
│  │ • VRSignalPayload schema                                │  │
│  │ • UnrealSignalPayload for UE                           │  │
│  │ • Example payloads                                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│       ↓                                                        │
│  Session Logger                                               │
│       ↓                                                        │
│  Output: JSON, VR, Unreal formats                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Signal Output Examples

### Per-Frame JSON Signal
```json
{
  "frame": 157,
  "timestamp": 5.234,
  "safety_flag": "warning",
  "confidence": 0.87,
  "severity": 2,
  "phase": "active",
  "correction": {
    "joint": "shoulder_left",
    "movement": "flexion",
    "direction": "lower",
    "target_angle": 120.0,
    "instruction": "Reduce shoulder flexion angle"
  },
  "is_new": true,
  "signal_code": "warning_shoulder_flexion_high_conf_active",
  "active_violations": 1,
  "primary_violation": "shoulder_left flexion"
}
```

### Unreal Engine Payload
```json
{
  "safety": {
    "status": "caution",
    "is_safe": true,
    "action_required": true,
    "command": "CORRECT_POSITION"
  },
  "confidence": {
    "value": 0.87,
    "severity": 2,
    "urgency": 1
  },
  "phase": {
    "name": "active",
    "confidence": 0.85
  },
  "correction": {
    "joint": "shoulder_left",
    "direction": "lower",
    "target": 120.0,
    "text": "Reduce shoulder flexion angle"
  },
  "haptic": {
    "intensity": 150,
    "duration_ms": 200
  }
}
```

---

## Medical Constraints Schema

### Joint + Movement + Phase Thresholds
```json
{
  "shoulder_flexion": {
    "rest": {"safe": 30, "caution": 60, "stop": 120},
    "initiation": {"safe": 45, "caution": 80, "stop": 120},
    "active": {"safe": 90, "caution": 110, "stop": 130},
    "transition": {"safe": 60, "caution": 90, "stop": 120},
    "completion": {"safe": 30, "caution": 45, "stop": 60}
  }
}
```

### Zones
- **SAFE**: Below caution threshold → continue exercise
- **CAUTION**: Between caution and stop → monitor closely
- **STOP**: At or above stop threshold → halt immediately

---

## Command Reference

| Command | Description |
|---------|-------------|
| `python main.py --mock` | Run with mock tracker |
| `python main.py --camera 0` | Run with webcam |
| `python run_demo.py --duration 900` | 15-min demo |
| `python run_demo.py --quick-test` | 60-sec quick test |
| `python test_system.py` | Run all tests |

---

## Output Files

After running a demo:
- `logs/{session}_signals.jsonl` - Per-frame signal data
- `logs/{session}_events.json` - Safety events
- `logs/{session}_session.json` - Complete session export

---

## Files Summary

| File | Purpose |
|------|---------|
| `config.json` | Safety thresholds configuration |
| `angle_utils.py` | Joint angle calculations |
| `safety_rules.py` | Safety assessment rules |
| `medical_constraints.py` | Medical grounding layer |
| `signal_generator.py` | Neuro-safe signal engine |
| `pose_tracker.py` | Webcam/MediaPipe tracking |
| `main.py` | Main application |
| `vr_signal_adapter.py` | VR/Unreal adapters |
| `session_logger.py` | Session logging |
| `run_demo.py` | Demo runner |
| `test_system.py` | Test suite |

---

## Medical Safety Notes

Important**: This system is designed as a safety aid, not⚠️ ** a replacement for professional medical supervision.

- Always have a qualified physiotherapist present during exercises
- The system provides guidance but cannot account for all individual conditions
- Patients should report any pain or discomfort immediately
- Safety thresholds should be adjusted by medical professionals for each patient

---

## Performance

| Metric | Value |
|--------|-------|
| Target FPS | 30 |
| Latency | < 50ms |
| Memory | < 100MB |
| CPU | < 30% |

---

## License

This project is provided for educational and medical safety purposes.
