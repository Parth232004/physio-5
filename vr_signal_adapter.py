"""
VR / Unreal Engine Signal Adapter Contract.

This module provides engine-agnostic signal schema and adapters
for VR and Unreal Engine consumption.

Python side only - no Unreal logic, just data formatting.
"""

import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

class SignalCategory(Enum):
    """Signal categories for VR systems"""
    SAFETY = "safety"
    PHASE = "phase"
    CORRECTION = "correction"
    METRICS = "metrics"


class UrgencyLevel(Enum):
    """Urgency levels for VR feedback"""
    LOW = 0      # Informational
    MEDIUM = 1   # Attention needed
    HIGH = 2     # Immediate action required
    CRITICAL = 3 # Emergency


@dataclass
class VRHapticConfig:
    """Haptic feedback configuration"""
    intensity: int  # 0-255
    duration_ms: int
    pattern: str  # "pulse", "continuous", "burst"
    
    def to_bytes(self) -> bytes:
        """Convert to byte representation for Unreal"""
        return bytes([
            self.intensity,
            (self.duration_ms >> 8) & 0xFF,
            self.duration_ms & 0xFF,
            0  # Reserved
        ])


@dataclass
class VRAudioConfig:
    """Audio cue configuration"""
    cue_id: str
    volume: float  # 0.0-1.0
    loop: bool
    priority: int  # 0-255
    
    def to_dict(self) -> Dict:
        return {
            "cue_id": self.cue_id,
            "volume": round(self.volume, 2),
            "loop": self.loop,
            "priority": self.priority
        }


@dataclass
class VRVisualConfig:
    """Visual indicator configuration"""
    color: str  # "green", "yellow", "red", "gray"
    opacity: float  # 0.0-1.0
    animation: str  # "solid", "pulse", "blink"
    position: str  # "hud", "joint", "screen"
    
    def to_dict(self) -> Dict:
        return {
            "color": self.color,
            "opacity": round(self.opacity, 2),
            "animation": self.animation,
            "position": self.position
        }


@dataclass
class VRSignalPayload:
    """
    Complete VR signal payload.
    Engine-agnostic schema for VR systems.
    """
    # Metadata
    signal_id: str
    timestamp: float
    frame_number: int
    
    # Safety data
    safety_flag: str  # "safe", "caution", "stop"
    confidence: float
    severity: int  # 0-3
    
    # Phase data
    phase: str  # "rest", "initiation", "active", "transition", "completion"
    phase_confidence: float
    
    # Correction data
    correction_enabled: bool
    correction_joint: Optional[str]
    correction_direction: Optional[str]
    correction_target: Optional[float]
    correction_instruction: Optional[str]
    
    # Feedback configurations
    haptic: Optional[VRHapticConfig]
    audio: Optional[VRAudioConfig]
    visual: Optional[VRVisualConfig]
    
    # Metrics
    processing_time_ms: float
    joint_count: int
    
    def to_dict(self) -> Dict:
        return {
            "meta": {
                "signal_id": self.signal_id,
                "timestamp": self.timestamp,
                "frame": self.frame_number,
                "datetime": datetime.fromtimestamp(self.timestamp).isoformat()
            },
            "safety": {
                "flag": self.safety_flag,
                "confidence": round(self.confidence, 3),
                "severity": self.severity
            },
            "phase": {
                "current": self.phase,
                "confidence": round(self.phase_confidence, 3)
            },
            "correction": {
                "enabled": self.correction_enabled,
                "joint": self.correction_joint,
                "direction": self.correction_direction,
                "target_angle": round(self.correction_target, 1) if self.correction_target else None,
                "instruction": self.correction_instruction
            },
            "feedback": {
                "haptic": {
                    "intensity": self.haptic.intensity,
                    "duration_ms": self.haptic.duration_ms,
                    "pattern": self.haptic.pattern
                } if self.haptic else None,
                "audio": self.audio.to_dict() if self.audio else None,
                "visual": self.visual.to_dict() if self.visual else None
            },
            "metrics": {
                "processing_time_ms": round(self.processing_time_ms, 2),
                "joint_count": self.joint_count
            }
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_unreal_bytes(self) -> bytes:
        """Serialize for Unreal Engine byte consumption"""
        # Format: [category:1][urgency:1][safety_flag:1][severity:1][confidence:4][phase:1][correction_flag:1][timestamp:8]
        import struct
        
        safety_map = {"safe": 0, "caution": 1, "stop": 2}
        phase_map = {"rest": 0, "initiation": 1, "active": 2, "transition": 3, "completion": 4}
        
        data = struct.pack(
            "!BBBBBfB1s",
            SignalCategory.SAFETY.value,
            UrgencyLevel.HIGH.value if self.severity >= 2 else UrgencyLevel.MEDIUM.value,
            safety_map.get(self.safety_flag, 0),
            self.severity,
            int(self.confidence * 255),
            self.processing_time_ms,
            phase_map.get(self.phase, 0),
            b'\x01' if self.correction_enabled else b'\x00'
        )
        
        return data


@dataclass
class UnrealSignalPayload:
    """
    Signal payload specifically formatted for Unreal Engine.
    """
    # Core safety
    safety_status: str
    is_safe: bool
    action_required: bool
    command_code: str
    
    # Confidence & severity
    confidence: float
    severity_level: int
    urgency: int
    
    # Phase
    exercise_phase: str
    phase_confidence: float
    
    # Correction
    correction_joint: Optional[str]
    correction_direction: Optional[str]
    correction_target: Optional[float]
    correction_text: Optional[str]
    
    # Display
    display_color: str
    display_icon: str
    display_text: str
    
    # Technical
    frame: int
    timestamp: float
    processing_time_ms: float
    
    # Haptic (for direct controller input)
    haptic_intensity: int
    haptic_duration_ms: int
    
    def to_dict(self) -> Dict:
        return {
            "safety": {
                "status": self.safety_status,
                "is_safe": self.is_safe,
                "action_required": self.action_required,
                "command": self.command_code
            },
            "confidence": {
                "value": round(self.confidence, 3),
                "severity": self.severity_level,
                "urgency": self.urgency
            },
            "phase": {
                "name": self.exercise_phase,
                "confidence": round(self.phase_confidence, 3)
            },
            "correction": {
                "joint": self.correction_joint,
                "direction": self.correction_direction,
                "target": round(self.correction_target, 1) if self.correction_target else None,
                "text": self.correction_text
            },
            "display": {
                "color": self.display_color,
                "icon": self.display_icon,
                "text": self.display_text
            },
            "technical": {
                "frame": self.frame,
                "timestamp": round(self.timestamp, 4),
                "processing_ms": round(self.processing_time_ms, 2)
            },
            "haptic": {
                "intensity": self.haptic_intensity,
                "duration_ms": self.haptic_duration_ms
            }
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# =============================================================================
# ADAPTER IMPLEMENTATION
# =============================================================================

class VRSignalAdapter:
    """
    VR Signal Adapter.
    
    Converts internal safety signals to VR/Unreal Engine formats.
    Python side only - no game engine logic.
    """
    
    # Haptic mappings based on severity
    HAPTIC_MAP = {
        0: VRHapticConfig(0, 50, "pulse"),
        1: VRHapticConfig(50, 100, "pulse"),
        2: VRHapticConfig(150, 200, "pulse"),
        3: VRHapticConfig(255, 500, "continuous")
    }
    
    # Audio mappings
    AUDIO_MAP = {
        "safe": VRAudioConfig("safety_safe", 0.5, False, 50),
        "caution": VRAudioConfig("safety_caution", 0.7, False, 100),
        "stop": VRAudioConfig("safety_stop", 1.0, True, 200)
    }
    
    # Visual mappings
    VISUAL_MAP = {
        "safe": VRVisualConfig("green", 0.8, "pulse", "hud"),
        "caution": VRVisualConfig("yellow", 0.9, "pulse", "hud"),
        "stop": VRVisualConfig("red", 1.0, "blink", "screen")
    }
    
    def __init__(self):
        self._signal_counter = 0
    
    def adapt(
        self,
        safety_flag: str,
        confidence: float,
        severity: int,
        phase: str,
        correction: Optional[Dict] = None,
        processing_time_ms: float = 0.0,
        joint_count: int = 0,
        timestamp: Optional[float] = None
    ) -> VRSignalPayload:
        """
        Adapt internal signal to VR payload.
        
        Args:
            safety_flag: "safe", "caution", "stop"
            confidence: 0.0-1.0
            severity: 0-3
            phase: Exercise phase
            correction: Optional correction data
            processing_time_ms: Processing time in ms
            joint_count: Number of joints tracked
            timestamp: Optional timestamp
            
        Returns:
            VRSignalPayload
        """
        self._signal_counter += 1
        
        # Determine correction data
        correction_enabled = correction is not None
        correction_joint = correction.get("joint") if correction else None
        correction_direction = correction.get("direction") if correction else None
        correction_target = correction.get("target_angle") if correction else None
        correction_instruction = correction.get("instruction") if correction else None
        
        # Get feedback configurations
        haptic = self.HAPTIC_MAP.get(severity, self.HAPTIC_MAP[0])
        audio = self.AUDIO_MAP.get(safety_flag, self.AUDIO_MAP["safe"])
        visual = self.VISUAL_MAP.get(safety_flag, self.VISUAL_MAP["safe"])
        
        return VRSignalPayload(
            signal_id=f"sig_{self._signal_counter:08x}",
            timestamp=timestamp or time.time(),
            frame_number=self._signal_counter,
            safety_flag=safety_flag,
            confidence=confidence,
            severity=severity,
            phase=phase,
            phase_confidence=confidence,  # Use same confidence
            correction_enabled=correction_enabled,
            correction_joint=correction_joint,
            correction_direction=correction_direction,
            correction_target=correction_target,
            correction_instruction=correction_instruction,
            haptic=haptic,
            audio=audio,
            visual=visual,
            processing_time_ms=processing_time_ms,
            joint_count=joint_count
        )
    
    def adapt_for_unreal(
        self,
        safety_flag: str,
        confidence: float,
        severity: int,
        phase: str,
        correction: Optional[Dict] = None,
        processing_time_ms: float = 0.0,
        frame_number: int = 0,
        timestamp: Optional[float] = None
    ) -> UnrealSignalPayload:
        """
        Adapt signal for Unreal Engine consumption.
        
        Args:
            safety_flag: "safe", "caution", "stop"
            confidence: 0.0-1.0
            severity: 0-3
            phase: Exercise phase
            correction: Optional correction data
            processing_time_ms: Processing time in ms
            frame_number: Current frame
            timestamp: Optional timestamp
            
        Returns:
            UnrealSignalPayload
        """
        # Command code mapping
        command_map = {
            "safe": "CONTINUE",
            "caution": "CORRECT_POSITION",
            "stop": "STOP_IMMEDIATELY"
        }
        
        # Display mappings
        color_map = {
            "safe": "Green",
            "caution": "Yellow",
            "stop": "Red"
        }
        
        icon_map = {
            "safe": "Checkmark",
            "caution": "Warning",
            "stop": "Error"
        }
        
        text_map = {
            "safe": "Position is correct",
            "caution": "Position needs correction",
            "stop": "STOP - Dangerous!"
        }
        
        # Correction data
        correction_joint = correction.get("joint") if correction else None
        correction_direction = correction.get("direction") if correction else None
        correction_target = correction.get("target_angle") if correction else None
        correction_text = correction.get("instruction") if correction else None
        
        # Haptic
        haptic = self.HAPTIC_MAP.get(severity, self.HAPTIC_MAP[0])
        
        return UnrealSignalPayload(
            safety_status=safety_flag,
            is_safe=(safety_flag == "safe"),
            action_required=(severity >= 2),
            command_code=command_map.get(safety_flag, "CONTINUE"),
            confidence=confidence,
            severity_level=severity,
            urgency=severity,
            exercise_phase=phase,
            phase_confidence=confidence,
            correction_joint=correction_joint,
            correction_direction=correction_direction,
            correction_target=correction_target,
            correction_text=correction_text,
            display_color=color_map.get(safety_flag, "Gray"),
            display_icon=icon_map.get(safety_flag, "None"),
            display_text=text_map.get(safety_flag, "Unknown"),
            frame=frame_number,
            timestamp=timestamp or time.time(),
            processing_time_ms=processing_time_ms,
            haptic_intensity=haptic.intensity,
            haptic_duration_ms=haptic.duration_ms
        )


# =============================================================================
# EXAMPLE PAYLOADS FOR UNREAL
# =============================================================================

EXAMPLE_PAYLOADS = {
    "safe_position": {
        "description": "Patient is in safe position",
        "payload": {
            "safety": {"status": "safe", "is_safe": True, "action_required": False, "command": "CONTINUE"},
            "confidence": {"value": 0.95, "severity": 0, "urgency": 0},
            "phase": {"name": "active", "confidence": 0.92},
            "correction": {"enabled": False, "joint": None, "direction": None, "target": None, "text": None},
            "display": {"color": "Green", "icon": "Checkmark", "text": "Position is correct"},
            "technical": {"frame": 157, "timestamp": 5.234, "processing_ms": 12.5},
            "haptic": {"intensity": 0, "duration_ms": 50}
        }
    },
    
    "caution_required": {
        "description": "Patient needs to adjust position",
        "payload": {
            "safety": {"status": "caution", "is_safe": True, "action_required": True, "command": "CORRECT_POSITION"},
            "confidence": {"value": 0.87, "severity": 2, "urgency": 1},
            "phase": {"name": "active", "confidence": 0.85},
            "correction": {
                "enabled": True,
                "joint": "shoulder_left",
                "direction": "lower",
                "target": 120.0,
                "text": "Reduce shoulder flexion angle"
            },
            "display": {"color": "Yellow", "icon": "Warning", "text": "Position needs correction"},
            "technical": {"frame": 234, "timestamp": 8.567, "processing_ms": 11.2},
            "haptic": {"intensity": 150, "duration_ms": 200}
        }
    },
    
    "stop_immediately": {
        "description": "Dangerous position - stop exercise",
        "payload": {
            "safety": {"status": "stop", "is_safe": False, "action_required": True, "command": "STOP_IMMEDIATELY"},
            "confidence": {"value": 0.98, "severity": 3, "urgency": 2},
            "phase": {"name": "active", "confidence": 0.96},
            "correction": {
                "enabled": True,
                "joint": "elbow_right",
                "direction": "straighten",
                "target": 10.0,
                "text": "Allow slight bend in elbow"
            },
            "display": {"color": "Red", "icon": "Error", "text": "STOP - Dangerous!"},
            "technical": {"frame": 312, "timestamp": 12.891, "processing_ms": 10.8},
            "haptic": {"intensity": 255, "duration_ms": 500}
        }
    },
    
    "phase_transition": {
        "description": "Phase change detected",
        "payload": {
            "safety": {"status": "safe", "is_safe": True, "action_required": False, "command": "CONTINUE"},
            "confidence": {"value": 0.91, "severity": 0, "urgency": 0},
            "phase": {"name": "transition", "confidence": 0.88},
            "correction": {"enabled": False, "joint": None, "direction": None, "target": None, "text": None},
            "display": {"color": "Green", "icon": "Arrow", "text": "Phase: Transition"},
            "technical": {"frame": 445, "timestamp": 18.234, "processing_ms": 13.1},
            "haptic": {"intensity": 0, "duration_ms": 50}
        }
    }
}


# =============================================================================
# SCHEMA DOCUMENTATION
# =============================================================================

SCHEMA_DOC = """
# VR / Unreal Engine Signal Schema

## VRSignalPayload

### Metadata
| Field | Type | Description |
|-------|------|-------------|
| signal_id | string | Unique signal identifier |
| timestamp | float | Unix timestamp |
| frame_number | int | Frame count |

### Safety Data
| Field | Type | Description |
|-------|------|-------------|
| safety_flag | string | "safe", "caution", "stop" |
| confidence | float | 0.0-1.0 |
| severity | int | 0-3 (INFO, LOW, MEDIUM, HIGH) |

### Phase Data
| Field | Type | Description |
|-------|------|-------------|
| phase | string | "rest", "initiation", "active", "transition", "completion" |
| phase_confidence | float | 0.0-1.0 |

### Correction Data
| Field | Type | Description |
|-------|------|-------------|
| correction_enabled | bool | Whether correction is needed |
| correction_joint | string | Joint to correct |
| correction_direction | string | Direction to adjust |
| correction_target | float | Target angle |
| correction_instruction | string | Human-readable instruction |

### Feedback
| Field | Type | Description |
|-------|------|-------------|
| haptic | object | Haptic configuration |
| audio | object | Audio cue configuration |
| visual | object | Visual indicator configuration |

## Unreal Integration

### Byte Protocol
```
[Category:1][Urgency:1][Safety:1][Severity:1][Confidence:1][Time:4][Phase:1][CorrectionFlag:1]
```

### C++ Struct Example
```cpp
struct FPhysioSafeSignal
{
    uint8 Category;       // SignalCategory::Safety
    uint8 Urgency;        // UrgencyLevel
    uint8 SafetyFlag;     // 0=Safe, 1=Caution, 2=Stop
    uint8 Severity;       // 0-3
    uint8 Confidence;     // 0-255 (scaled)
    float ProcessingTime;
    uint8 Phase;          // 0-4
    bool bNeedsCorrection;
};
```

## JSON Examples
See `EXAMPLE_PAYLOADS` for complete examples.
"""
