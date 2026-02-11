"""
Fail-Safe Visual Alert System for PhysioSafe VR Safety System.

Provides visual demonstration of fail-safe alerts for:
- Console output (for testing/demo)
- VR integration hooks
- Unreal Engine visualization

This module ensures that danger conditions are immediately
visible and actionable by both the patient and therapist.
"""

import time
import json
from dataclasses import dataclass
from typing import Dict, Optional, Callable
from enum import Enum
from signal_generator import SafetyFrameSignal, ExercisePhase


class AlertType(Enum):
    """Types of visual alerts"""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    DANGER = "danger"


class VisualStyle(Enum):
    """Visual styling options"""
    CONSOLE = "console"
    VR = "vr"
    UNREAL = "unreal"
    MINIMAL = "minimal"


@dataclass
class FailSafeAlert:
    """Complete fail-safe alert data"""
    alert_type: AlertType
    frame_number: int
    timestamp: float
    confidence: float
    severity: int
    phase: str
    primary_violation: Optional[str]
    current_angle: Optional[float]
    safe_limit: Optional[float]
    instruction: Optional[str]
    is_new: bool
    
    def to_dict(self) -> Dict:
        return {
            "alert_type": self.alert_type.value,
            "frame": self.frame_number,
            "timestamp": round(self.timestamp, 4),
            "confidence": round(self.confidence, 3),
            "severity": self.severity,
            "phase": self.phase,
            "primary_violation": self.primary_violation,
            "current_angle": self.current_angle,
            "safe_limit": self.safe_limit,
            "instruction": self.instruction,
            "is_new": self.is_new
        }


class FailSafeVisualizer:
    """
    Visual alert system for fail-safe conditions.
    
    Provides multiple output formats:
    - Console: ASCII art alerts for demos
    - VR: Haptic/audio/visual configuration
    - Unreal: Blueprint-ready data structures
    - Minimal: Compact status indicators
    """
    
    # Alert configurations
    ALERT_CONFIGS = {
        AlertType.SAFE: {
            "icon": "✓",
            "color": "\033[92m",  # Green
            "vr_color": "green",
            "urgency": 0,
            "haptic_intensity": 0,
            "haptic_duration": 50,
            "audio_cue": "safety_safe",
            "visual_animation": "pulse"
        },
        AlertType.CAUTION: {
            "icon": "⚠",
            "color": "\033[93m",  # Yellow
            "vr_color": "yellow",
            "urgency": 1,
            "haptic_intensity": 50,
            "haptic_duration": 100,
            "audio_cue": "safety_caution",
            "visual_animation": "pulse"
        },
        AlertType.WARNING: {
            "icon": "⚠",
            "color": "\033[93m",  # Yellow
            "vr_color": "yellow",
            "urgency": 2,
            "haptic_intensity": 150,
            "haptic_duration": 200,
            "audio_cue": "safety_caution",
            "visual_animation": "pulse"
        },
        AlertType.DANGER: {
            "icon": "✗",
            "color": "\033[91m",  # Red
            "vr_color": "red",
            "urgency": 3,
            "haptic_intensity": 255,
            "haptic_duration": 500,
            "audio_cue": "safety_stop",
            "visual_animation": "blink"
        }
    }
    
    RESET_COLOR = "\033[0m"
    
    def __init__(
        self,
        style: VisualStyle = VisualStyle.CONSOLE,
        alert_callback: Optional[Callable[[FailSafeAlert], None]] = None,
        min_severity_for_alert: int = 1
    ):
        """
        Initialize fail-safe visualizer.
        
        Args:
            style: Output style (console, vr, unreal, minimal)
            alert_callback: Optional callback for custom alert handling
            min_severity_for_alert: Minimum severity to trigger alerts (0-3)
        """
        self.style = style
        self.alert_callback = alert_callback
        self.min_severity_for_alert = min_severity_for_alert
        
        # Alert tracking
        self.current_alert: Optional[FailSafeAlert] = None
        self.alert_count = 0
        self.danger_count = 0
        self.last_alert_time = 0
        
        # Statistics
        self.stats = {
            "safe_alerts": 0,
            "caution_alerts": 0,
            "warning_alerts": 0,
            "danger_alerts": 0,
            "total_alerts": 0
        }
    
    def process_signal(self, signal: SafetyFrameSignal) -> Optional[FailSafeAlert]:
        """
        Process a safety signal and generate visual alert.
        
        Args:
            signal: SafetyFrameSignal from the system
            
        Returns:
            FailSafeAlert if alert should be displayed
        """
        # Determine alert type from safety flag
        alert_type = self._safety_flag_to_alert_type(signal.safety_flag)
        
        # Create alert data
        alert = FailSafeAlert(
            alert_type=alert_type,
            frame_number=signal.frame_number,
            timestamp=signal.timestamp,
            confidence=signal.confidence,
            severity=signal.severity,
            phase=signal.phase,
            primary_violation=signal.primary_violation,
            current_angle=signal.correction.get("target_angle") if signal.correction else None,
            safe_limit=None,
            instruction=signal.correction.get("instruction") if signal.correction else None,
            is_new=signal.is_new
        )
        
        # Check if we should display alert
        if signal.severity >= self.min_severity_for_alert:
            self._display_alert(alert)
            self.current_alert = alert
            self.alert_count += 1
            self.stats["total_alerts"] += 1
            self.stats[f"{alert_type.value}_alerts"] += 1
            
            if alert_type == AlertType.DANGER:
                self.danger_count += 1
            
            # Call callback if set
            if self.alert_callback:
                self.alert_callback(alert)
            
            return alert
        
        return None
    
    def _safety_flag_to_alert_type(self, safety_flag: str) -> AlertType:
        """Convert safety flag to alert type"""
        mapping = {
            "safe": AlertType.SAFE,
            "caution": AlertType.CAUTION,
            "warning": AlertType.WARNING,
            "danger": AlertType.DANGER,
            "unknown": AlertType.CAUTION
        }
        return mapping.get(safety_flag, AlertType.CAUTION)
    
    def _display_alert(self, alert: FailSafeAlert):
        """Display alert based on configured style"""
        if self.style == VisualStyle.CONSOLE:
            self._display_console_alert(alert)
        elif self.style == VisualStyle.VR:
            self._display_vr_alert(alert)
        elif self.style == VisualStyle.UNREAL:
            self._display_unreal_alert(alert)
        elif self.style == VisualStyle.MINIMAL:
            self._display_minimal_alert(alert)
    
    def _display_console_alert(self, alert: FailSafeAlert):
        """Display ASCII art alert for console"""
        config = self.ALERT_CONFIGS[alert.alert_type]
        
        if alert.severity >= 3:
            # Full fail-safe display for danger
            self._print_fail_safe(alert, config)
        elif alert.severity >= 2:
            # Warning display
            self._print_warning(alert, config)
        else:
            # Simple info display
            self._print_info(alert, config)
    
    def _print_fail_safe(self, alert: FailSafeAlert, config: Dict):
        """Print full fail-safe alert"""
        print("\n" + "═" * 66)
        print(f"  {config['icon']}  FAIL-SAFE ACTIVATED  {config['icon']}")
        print("═" * 66)
        print(f"  FRAME: {alert.frame_number:5d}  |  TIME: {alert.timestamp:7.3f}s")
        print(f"  SAFETY: {alert.alert_type.value.upper():7s}  |  SEVERITY: {alert.severity} (CRITICAL)")
        print(f"  CONFIDENCE: {alert.confidence:.1%}  |  PHASE: {alert.phase}")
        print("─" * 66)
        if alert.primary_violation:
            print(f"  VIOLATION: {alert.primary_violation}")
        if alert.instruction:
            print(f"  INSTRUCTION: {alert.instruction}")
        print("─" * 66)
        print(f"  ⚠️  ⚠️  ⚠️  STOP EXERCISE IMMEDIATELY  ⚠️  ⚠️  ⚠️")
        print("═" * 66 + "\n")
    
    def _print_warning(self, alert: FailSafeAlert, config: Dict):
        """Print warning alert"""
        print(f"\n{config['icon']} [{alert.alert_type.upper()}] Frame {alert.frame_number}")
        print(f"   Confidence: {alert.confidence:.1%} | Phase: {alert.phase}")
        if alert.instruction:
            print(f"   → {alert.instruction}")
        print(self.RESET_COLOR, end="", flush=True)
    
    def _print_info(self, alert: FailSafeAlert, config: Dict):
        """Print info alert"""
        print(f"{config['icon']} [{alert.phase}] Frame {alert.frame_number}")
        print(f"   Confidence: {alert.confidence:.1%}")
        print(self.RESET_COLOR, end="", flush=True)
    
    def _display_vr_alert(self, alert: FailSafeAlert) -> Dict:
        """Generate VR-specific alert configuration"""
        config = self.ALERT_CONFIGS[alert.alert_type]
        
        vr_alert = {
            "alert_type": alert.alert_type.value,
            "visual": {
                "color": config["vr_color"],
                "opacity": 1.0 if alert.severity >= 2 else 0.8,
                "animation": config["visual_animation"],
                "position": "screen" if alert.severity >= 3 else "hud",
                "size": "fullscreen" if alert.severity >= 3 else "normal"
            },
            "haptic": {
                "enabled": alert.severity >= 1,
                "intensity": config["haptic_intensity"],
                "duration_ms": config["haptic_duration"],
                "pattern": "continuous" if alert.severity >= 3 else "pulse"
            },
            "audio": {
                "cue_id": config["audio_cue"],
                "volume": 1.0 if alert.severity >= 2 else 0.7,
                "loop": alert.severity >= 3,
                "priority": config["urgency"] * 100
            },
            "text": {
                "message": alert.instruction or "Position is correct",
                "size": "large" if alert.severity >= 2 else "normal",
                "color": config["vr_color"]
            },
            "technical": {
                "frame": alert.frame_number,
                "timestamp": alert.timestamp,
                "confidence": alert.confidence,
                "severity": alert.severity
            }
        }
        
        return vr_alert
    
    def _display_unreal_alert(self, alert: FailSafeAlert) -> Dict:
        """Generate Unreal Engine-ready alert data"""
        config = self.ALERT_CONFIGS[alert.alert_type]
        
        unreal_alert = {
            "fail_safe": {
                "activated": alert.severity >= 3,
                "severity": alert.severity,
                "urgency": config["urgency"]
            },
            "display": {
                "color": config["vr_color"].upper(),
                "visibility": "visible" if alert.severity >= 1 else "hidden",
                "animation": config["visual_animation"]
            },
            "haptic": {
                "controller_left": {
                    "intensity": config["haptic_intensity"],
                    "duration": config["haptic_duration"]
                },
                "controller_right": {
                    "intensity": config["haptic_intensity"],
                    "duration": config["haptic_duration"]
                }
            },
            "audio": {
                "cue": config["audio_cue"],
                "volume": 1.0 if alert.severity >= 2 else 0.7,
                "looping": alert.severity >= 3
            },
            "overlay": {
                "show_overlay": alert.severity >= 2,
                "overlay_text": alert.instruction or "",
                "overlay_color": config["vr_color"].upper()
            },
            "bp_event": f"BP_OnSafetyAlert_{alert.alert_type.value.upper()}"
        }
        
        return unreal_alert
    
    def _display_minimal_alert(self, alert: FailSafeAlert):
        """Display minimal status indicator"""
        icons = {
            AlertType.SAFE: "●",
            AlertType.CAUTION: "◐",
            AlertType.WARNING: "◑",
            AlertType.DANGER: "■"
        }
        
        icon = icons.get(alert.alert_type, "?")
        color = self.ALERT_CONFIGS[alert.alert_type]["color"]
        
        print(f"{color}{icon}{self.RESET_COLOR}", end="", flush=True)
    
    def get_statistics(self) -> Dict:
        """Get alert statistics"""
        return {
            **self.stats,
            "current_alert": self.current_alert.to_dict() if self.current_alert else None,
            "danger_count": self.danger_count,
            "alert_count": self.alert_count
        }
    
    def reset(self):
        """Reset visualizer state"""
        self.current_alert = None
        self.alert_count = 0
        self.danger_count = 0
        self.stats = {
            "safe_alerts": 0,
            "caution_alerts": 0,
            "warning_alerts": 0,
            "danger_alerts": 0,
            "total_alerts": 0
        }
    
    def demo_sequence(self):
        """Demonstrate all alert types"""
        print("\n=== FAIL-SAFE VISUALIZER DEMO ===\n")
        
        # Create demo signals
        from signal_generator import SafetyFrameSignal, CorrectionGuidance
        
        demo_signals = [
            SafetyFrameSignal(
                frame_number=1, timestamp=0.0,
                safety_flag="safe", confidence=0.95, severity=0, phase="rest",
                correction=None, is_new=True, signal_code="safe_clean",
                active_violations=0, primary_violation=None
            ),
            SafetyFrameSignal(
                frame_number=2, timestamp=0.1,
                safety_flag="warning", confidence=0.85, severity=2, phase="active",
                correction={"joint": "shoulder_left", "direction": "lower", "target_angle": 120, "instruction": "Reduce shoulder flexion"},
                is_new=True, signal_code="warning_shoulder_flexion",
                active_violations=1, primary_violation="shoulder_left flexion"
            ),
            SafetyFrameSignal(
                frame_number=3, timestamp=0.2,
                safety_flag="danger", confidence=0.95, severity=3, phase="active",
                correction={"joint": "elbow_right", "direction": "straighten", "target_angle": 0, "instruction": "STOP - Hyperextension detected"},
                is_new=True, signal_code="danger_elbow_extension",
                active_violations=1, primary_violation="elbow_right extension"
            )
        ]
        
        print("\n--- Console Style ---")
        for signal in demo_signals:
            self.process_signal(signal)
            time.sleep(0.5)
        
        print("\n--- Statistics ---")
        print(self.get_statistics())
        
        print("\n--- VR Output (Danger) ---")
        vr_alert = self._display_vr_alert(self.current_alert)
        print(json.dumps(vr_alert, indent=2))
        
        print("\n--- Unreal Output (Danger) ---")
        unreal_alert = self._display_unreal_alert(self.current_alert)
        print(json.dumps(unreal_alert, indent=2))
        
        print("\n=== DEMO COMPLETE ===\n")


def create_fail_safe_callback(style: VisualStyle = VisualStyle.CONSOLE) -> Callable:
    """
    Create a fail-safe callback for integration with main system.
    
    Usage:
        visualizer = FailSafeVisualizer(style=VisualStyle.CONSOLE)
        callback = create_fail_safe_callback(VisualStyle.CONSOLE)
        
        # In main loop:
        signal = engine.process_frame(assessment)
        callback(signal)
    """
    visualizer = FailSafeVisualizer(style=style)
    
    def callback(signal: SafetyFrameSignal):
        visualizer.process_signal(signal)
    
    return callback


if __name__ == "__main__":
    # Run demo
    visualizer = FailSafeVisualizer(style=VisualStyle.CONSOLE)
    visualizer.demo_sequence()
