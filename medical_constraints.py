"""
Medical Grounding Layer for PhysioSafe VR Safety System.

This module encodes safe/caution/stop ranges per joint + phase.
Rule-based, configurable thresholds - deterministic medical validation layer.
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from angle_utils import Point3D


class MedicalZone(Enum):
    """Medical safety zones"""
    SAFE = "safe"
    CAUTION = "caution"
    STOP = "stop"


class JointType(Enum):
    """Upper body joint types"""
    SHOULDER_LEFT = "shoulder_left"
    SHOULDER_RIGHT = "shoulder_right"
    ELBOW_LEFT = "elbow_left"
    ELBOW_RIGHT = "elbow_right"
    WRIST_LEFT = "wrist_left"
    WRIST_RIGHT = "wrist_right"


class MovementType(Enum):
    """Types of joint movements"""
    FLEXION = "flexion"
    EXTENSION = "extension"
    ABDUCTION = "abduction"
    ADDUCTION = "adduction"


class ExercisePhase(Enum):
    """Exercise phases for phase-dependent constraints"""
    REST = "rest"
    INITIATION = "initiation"
    ACTIVE = "active"
    TRANSITION = "transition"
    COMPLETION = "completion"


@dataclass
class MedicalThreshold:
    """
    Medical threshold for a specific joint + movement + phase.
    
    Attributes:
        joint: Joint identifier
        movement: Movement type
        phase: Exercise phase (None = all phases)
        safe_max: Maximum angle for safe zone
        caution_max: Maximum angle for caution zone
        stop_max: Maximum angle before stop
        unit: Unit of measurement (degrees)
    """
    joint: str
    movement: str
    phase: Optional[str]
    safe_max: float
    caution_max: float
    stop_max: float
    unit: str = "degrees"
    
    def get_zone(self, angle: float) -> MedicalZone:
        """Determine medical zone based on angle"""
        if angle >= self.stop_max:
            return MedicalZone.STOP
        elif angle >= self.caution_max:
            return MedicalZone.CAUTION
        else:
            return MedicalZone.SAFE
    
    def to_dict(self) -> Dict:
        return {
            "joint": self.joint,
            "movement": self.movement,
            "phase": self.phase,
            "safe_max": self.safe_max,
            "caution_max": self.caution_max,
            "stop_max": self.stop_max,
            "unit": self.unit
        }


@dataclass
class MedicalViolation:
    """Represents a medical constraint violation"""
    joint: str
    movement: str
    phase: str
    current_angle: float
    expected_zone: MedicalZone
    actual_zone: MedicalZone
    threshold: MedicalThreshold
    severity_score: int  # 0-10
    recommendation: str
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            "joint": self.joint,
            "movement": self.movement,
            "phase": self.phase,
            "current_angle": round(self.current_angle, 2),
            "expected_zone": self.expected_zone.value,
            "actual_zone": self.actual_zone.value,
            "severity_score": self.severity_score,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp
        }


@dataclass
class MedicalValidationResult:
    """Result of medical constraint validation"""
    is_valid: bool
    overall_zone: MedicalZone
    violations: List[MedicalViolation]
    warnings: List[str]
    timestamp: float
    frame_number: int
    
    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid,
            "overall_zone": self.overall_zone.value,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "timestamp": self.timestamp,
            "frame_number": self.frame_number
        }


class MedicalConstraints:
    """
    Medical grounding layer with phase-dependent constraints.
    Deterministic rule-based validation for physiotherapy exercises.
    """
    
    # Default thresholds for upper body (degrees)
    DEFAULT_THRESHOLDS = {
        # Shoulder movements
        "shoulder_flexion": {
            "rest": {"safe": 30, "caution": 60, "stop": 120},
            "initiation": {"safe": 45, "caution": 80, "stop": 120},
            "active": {"safe": 90, "caution": 110, "stop": 130},
            "transition": {"safe": 60, "caution": 90, "stop": 120},
            "completion": {"safe": 30, "caution": 45, "stop": 60}
        },
        "shoulder_abduction": {
            "rest": {"safe": 20, "caution": 45, "stop": 90},
            "initiation": {"safe": 45, "caution": 90, "stop": 150},
            "active": {"safe": 90, "caution": 120, "stop": 160},
            "transition": {"safe": 60, "caution": 90, "stop": 120},
            "completion": {"safe": 20, "caution": 40, "stop": 60}
        },
        "shoulder_extension": {
            "rest": {"safe": 10, "caution": 20, "stop": 45},
            "initiation": {"safe": 15, "caution": 30, "stop": 50},
            "active": {"safe": 30, "caution": 45, "stop": 60},
            "transition": {"safe": 20, "caution": 35, "stop": 50},
            "completion": {"safe": 10, "caution": 20, "stop": 30}
        },
        # Elbow movements
        "elbow_flexion": {
            "rest": {"safe": 30, "caution": 60, "stop": 120},
            "initiation": {"safe": 45, "caution": 90, "stop": 140},
            "active": {"safe": 90, "caution": 120, "stop": 150},
            "transition": {"safe": 60, "caution": 90, "stop": 120},
            "completion": {"safe": 30, "caution": 45, "stop": 60}
        },
        "elbow_extension": {
            "rest": {"safe": 5, "caution": 8, "stop": 10},
            "initiation": {"safe": 5, "caution": 8, "stop": 10},
            "active": {"safe": 8, "caution": 10, "stop": 15},
            "transition": {"safe": 5, "caution": 8, "stop": 10},
            "completion": {"safe": 3, "caution": 5, "stop": 8}
        },
        # Wrist movements
        "wrist_flexion": {
            "rest": {"safe": 20, "caution": 40, "stop": 70},
            "initiation": {"safe": 30, "caution": 50, "stop": 80},
            "active": {"safe": 50, "caution": 65, "stop": 85},
            "transition": {"safe": 30, "caution": 50, "stop": 70},
            "completion": {"safe": 15, "caution": 30, "stop": 50}
        },
        "wrist_extension": {
            "rest": {"safe": 15, "caution": 35, "stop": 60},
            "initiation": {"safe": 25, "caution": 45, "stop": 70},
            "active": {"safe": 45, "caution": 60, "stop": 75},
            "transition": {"safe": 30, "caution": 45, "stop": 60},
            "completion": {"safe": 15, "caution": 25, "stop": 40}
        }
    }
    
    # Severity recommendations
    RECOMMENDATIONS = {
        ("shoulder", "flexion"): {
            MedicalZone.STOP: "Stop immediately. Return arm to neutral position.",
            MedicalZone.CAUTION: "Reduce shoulder flexion. Stay below 90 during active phase."
        },
        ("shoulder", "abduction"): {
            MedicalZone.STOP: "Stop immediately. Lower arm to side.",
            MedicalZone.CAUTION: "Limit abduction to below 120."
        },
        ("elbow", "flexion"): {
            MedicalZone.STOP: "Stop immediately. Straighten elbow.",
            MedicalZone.CAUTION: "Avoid full flexion beyond 120."
        },
        ("elbow", "extension"): {
            MedicalZone.STOP: "Stop immediately. Allow slight bend in elbow.",
            MedicalZone.CAUTION: "Avoid hyperextension beyond 5."
        },
        ("wrist", "flexion"): {
            MedicalZone.STOP: "Stop immediately. Return wrist to neutral.",
            MedicalZone.CAUTION: "Limit flexion to below 65."
        },
        ("wrist", "extension"): {
            MedicalZone.STOP: "Stop immediately. Return wrist to neutral.",
            MedicalZone.CAUTION: "Limit extension to below 60."
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize medical constraints layer.
        
        Args:
            config_path: Optional path to custom threshold config
        """
        if config_path:
            with open(config_path, 'r') as f:
                self.thresholds = json.load(f)
        else:
            self.thresholds = self.DEFAULT_THRESHOLDS.copy()
    
    def get_threshold(
        self,
        joint: str,
        movement: str,
        phase: str
    ) -> Optional[MedicalThreshold]:
        """Get threshold for specific joint + movement + phase"""
        key = f"{joint}_{movement}"
        
        if key not in self.thresholds:
            return None
        
        phase_thresholds = self.thresholds[key].get(phase)
        
        if not phase_thresholds:
            phase_thresholds = self.thresholds[key].get("active")
        
        if not phase_thresholds:
            return None
        
        return MedicalThreshold(
            joint=joint,
            movement=movement,
            phase=phase,
            safe_max=phase_thresholds["safe"],
            caution_max=phase_thresholds["caution"],
            stop_max=phase_thresholds["stop"]
        )
    
    def validate(
        self,
        angles: Dict[str, float],
        phase: str,
        timestamp: float = 0.0,
        frame_number: int = 0
    ) -> MedicalValidationResult:
        """
        Validate angles against medical constraints.
        
        Args:
            angles: Dictionary of angle_name -> value
            phase: Current exercise phase
            timestamp: Current timestamp
            frame_number: Current frame number
            
        Returns:
            MedicalValidationResult
        """
        violations = []
        warnings = []
        highest_zone = MedicalZone.SAFE
        
        for angle_name, angle_value in angles.items():
            # Parse angle name
            parts = angle_name.split('_')
            if len(parts) < 3:
                continue
            
            # Extract joint and movement
            side = parts[0]  # left/right
            joint = '_'.join(parts[:-1])  # shoulder_left, elbow_left, etc.
            movement = parts[-1]  # flexion, abduction, etc.
            
            # Get threshold
            threshold = self.get_threshold(joint, movement, phase)
            
            if not threshold:
                continue
            
            # Determine zone
            actual_zone = threshold.get_zone(angle_value)
            
            if actual_zone == MedicalZone.STOP:
                highest_zone = MedicalZone.STOP
                
                # Calculate severity score (0-10)
                severity = min(10, int((angle_value - threshold.caution_max) / 
                                        (threshold.stop_max - threshold.caution_max) * 5 + 5))
                
                # Get recommendation
                recommendation = self.RECOMMENDATIONS.get(
                    (joint.split('_')[-1], movement), {}
                ).get(actual_zone, "Consult with physiotherapist.")
                
                violation = MedicalViolation(
                    joint=joint,
                    movement=movement,
                    phase=phase,
                    current_angle=angle_value,
                    expected_zone=MedicalZone.SAFE,
                    actual_zone=actual_zone,
                    threshold=threshold,
                    severity_score=severity,
                    recommendation=recommendation,
                    timestamp=timestamp
                )
                violations.append(violation)
                
            elif actual_zone == MedicalZone.CAUTION:
                if highest_zone != MedicalZone.STOP:
                    highest_zone = MedicalZone.CAUTION
                
                warnings.append(f"{joint} {movement} at {angle_value:.1f}° - caution zone")
        
        return MedicalValidationResult(
            is_valid=highest_zone != MedicalZone.STOP,
            overall_zone=highest_zone,
            violations=violations,
            warnings=warnings,
            timestamp=timestamp,
            frame_number=frame_number
        )
    
    def export_config(self, filepath: str):
        """Export current configuration to file"""
        with open(filepath, 'w') as f:
            json.dump(self.thresholds, f, indent=2)
    
    def get_joints(self) -> List[str]:
        """Get list of supported joints"""
        return list(set(
            '_'.join(k.split('_')[:-1]) 
            for k in self.thresholds.keys()
        ))
    
    def get_movements(self, joint: str) -> List[str]:
        """Get list of movements for a joint"""
        movements = []
        prefix = f"{joint}_"
        for key in self.thresholds.keys():
            if key.startswith(prefix):
                movements.append(key.replace(prefix, ''))
        return movements


# Example usage and schema documentation
MEDICAL_SCHEMA_DOC = """
# Medical Constraints Schema

## Joint + Movement + Phase Thresholds

{
    "shoulder_flexion": {
        "rest": {"safe": 30, "caution": 60, "stop": 120},
        "initiation": {"safe": 45, "caution": 80, "stop": 120},
        "active": {"safe": 90, "caution": 110, "stop": 130},
        "transition": {"safe": 60, "caution": 90, "stop": 120},
        "completion": {"safe": 30, "caution": 45, "stop": 60}
    },
    ...
}

## Zones
- **SAFE**: Below caution threshold - continue exercise
- **CAUTION**: Between caution and stop - monitor closely
- **STOP**: At or above stop threshold - halt immediately
"""
