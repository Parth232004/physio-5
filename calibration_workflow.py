"""
Clinician Calibration Workflow for PhysioSafe VR Safety System.

Provides a guided calibration process for clinicians to:
1. Set patient-specific safety thresholds
2. Calibrate tracking sensitivity
3. Validate safety limits before exercise session
4. Save/load calibration profiles

Clinical Context:
- Different patients have different mobility levels
- Age, injury history, and surgery type affect safe ranges
- Calibration ensures personalized safety thresholds
"""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path


class PatientMobilityLevel(Enum):
    """Patient mobility classification for default thresholds"""
    NORMAL = "normal"           # Full mobility, no restrictions
    LIMITED = "limited"         # Some ROM restrictions
    RESTRICTED = "restricted"  # Significant ROM limitations
    POST_SURGICAL = "post_surgical"  # Recently surgically treated
    REHABILITATION = "rehabilitation"  # Active rehabilitation phase


class CalibrationState(Enum):
    """Calibration workflow states"""
    NOT_STARTED = "not_started"
    PATIENT_INFO = "patient_info"
    MOBILITY_ASSESSMENT = "mobility_assessment"
    RANGE_OF_MOTION = "range_of_motion"
    SAFETY_LIMIT_SETTING = "safety_limit_setting"
    VALIDATION = "validation"
    COMPLETED = "completed"


@dataclass
class PatientInfo:
    """Patient demographic and clinical information"""
    patient_id: str
    age: int
    mobility_level: PatientMobilityLevel
    injury_history: List[str] = field(default_factory=list)
    surgery_type: Optional[str] = None
    surgery_date: Optional[str] = None
    therapist_notes: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass
class CalibrationProfile:
    """Complete calibration profile for a patient"""
    profile_id: str
    patient_info: PatientInfo
    mobility_level: PatientMobilityLevel
    
    # Joint-specific calibrated thresholds (degrees)
    shoulder_flexion_safe: float = 120
    shoulder_flexion_warning: float = 100
    shoulder_extension_safe: float = 60
    shoulder_extension_warning: float = 45
    shoulder_abduction_safe: float = 150
    shoulder_abduction_warning: float = 120
    
    elbow_flexion_safe: float = 150
    elbow_flexion_warning: float = 120
    elbow_extension_safe: float = 10
    elbow_extension_warning: float = 5
    
    wrist_flexion_safe: float = 80
    wrist_flexion_warning: float = 60
    wrist_extension_safe: float = 70
    wrist_extension_warning: float = 55
    
    # Tracking confidence threshold
    confidence_threshold: float = 0.6
    
    # Calibration metadata
    calibrated_at: float = field(default_factory=time.time)
    calibrated_by: str = ""
    validation_passed: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "profile_id": self.profile_id,
            "patient_info": {
                "patient_id": self.patient_info.patient_id,
                "age": self.patient_info.age,
                "mobility_level": self.patient_info.mobility_level.value,
                "injury_history": self.patient_info.injury_history,
                "surgery_type": self.patient_info.surgery_type,
                "surgery_date": self.patient_info.surgery_date,
                "therapist_notes": self.patient_info.therapist_notes
            },
            "mobility_level": self.mobility_level.value,
            "thresholds": {
                "shoulder": {
                    "flexion": {"safe": self.shoulder_flexion_safe, "warning": self.shoulder_flexion_warning},
                    "extension": {"safe": self.shoulder_extension_safe, "warning": self.shoulder_extension_warning},
                    "abduction": {"safe": self.shoulder_abduction_safe, "warning": self.shoulder_abduction_warning}
                },
                "elbow": {
                    "flexion": {"safe": self.elbow_flexion_safe, "warning": self.elbow_flexion_warning},
                    "extension": {"safe": self.elbow_extension_safe, "warning": self.elbow_extension_warning}
                },
                "wrist": {
                    "flexion": {"safe": self.wrist_flexion_safe, "warning": self.wrist_flexion_warning},
                    "extension": {"safe": self.wrist_extension_safe, "warning": self.wrist_extension_warning}
                }
            },
            "confidence_threshold": self.confidence_threshold,
            "calibrated_at": self.calibrated_at,
            "calibrated_by": self.calibrated_by,
            "validation_passed": self.validation_passed,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CalibrationProfile':
        """Create from dictionary"""
        patient_info = PatientInfo(
            patient_id=data["patient_info"]["patient_id"],
            age=data["patient_info"]["age"],
            mobility_level=PatientMobilityLevel(data["patient_info"]["mobility_level"]),
            injury_history=data["patient_info"].get("injury_history", []),
            surgery_type=data["patient_info"].get("surgery_type"),
            surgery_date=data["patient_info"].get("surgery_date"),
            therapist_notes=data["patient_info"].get("therapist_notes", "")
        )
        
        thresholds = data.get("thresholds", {})
        shoulder = thresholds.get("shoulder", {})
        elbow = thresholds.get("elbow", {})
        wrist = thresholds.get("wrist", {})
        
        profile = cls(
            profile_id=data["profile_id"],
            patient_info=patient_info,
            mobility_level=PatientMobilityLevel(data["mobility_level"]),
            shoulder_flexion_safe=shoulder.get("flexion", {}).get("safe", 120),
            shoulder_flexion_warning=shoulder.get("flexion", {}).get("warning", 100),
            shoulder_extension_safe=shoulder.get("extension", {}).get("safe", 60),
            shoulder_extension_warning=shoulder.get("extension", {}).get("warning", 45),
            shoulder_abduction_safe=shoulder.get("abduction", {}).get("safe", 150),
            shoulder_abduction_warning=shoulder.get("abduction", {}).get("warning", 120),
            elbow_flexion_safe=elbow.get("flexion", {}).get("safe", 150),
            elbow_flexion_warning=elbow.get("flexion", {}).get("warning", 120),
            elbow_extension_safe=elbow.get("extension", {}).get("safe", 10),
            elbow_extension_warning=elbow.get("extension", {}).get("warning", 5),
            wrist_flexion_safe=wrist.get("flexion", {}).get("safe", 80),
            wrist_flexion_warning=wrist.get("flexion", {}).get("warning", 60),
            wrist_extension_safe=wrist.get("extension", {}).get("safe", 70),
            wrist_extension_warning=wrist.get("extension", {}).get("warning", 55),
            confidence_threshold=data.get("confidence_threshold", 0.6),
            calibrated_by=data.get("calibrated_by", ""),
            validation_passed=data.get("validation_passed", False),
            notes=data.get("notes", "")
        )
        
        if "calibrated_at" in data:
            profile.calibrated_at = data["calibrated_at"]
        
        return profile
    
    def to_safety_rules_config(self) -> Dict:
        """Convert to safety rules configuration format"""
        return {
            "shoulder": {
                "flexion": {"safe_max": self.shoulder_flexion_safe, "warning_max": self.shoulder_flexion_warning},
                "extension": {"safe_max": self.shoulder_extension_safe, "warning_max": self.shoulder_extension_warning},
                "abduction": {"safe_max": self.shoulder_abduction_safe, "warning_max": self.shoulder_abduction_warning}
            },
            "elbow": {
                "flexion": {"safe_max": self.elbow_flexion_safe, "warning_max": self.elbow_flexion_warning},
                "extension": {"safe_max": self.elbow_extension_safe, "warning_max": self.elbow_extension_warning}
            },
            "wrist": {
                "flexion": {"safe_max": self.wrist_flexion_safe, "warning_max": self.wrist_flexion_warning},
                "extension": {"safe_max": self.wrist_extension_safe, "warning_max": self.wrist_extension_warning}
            }
        }


# Default thresholds by mobility level
MOBILITY_DEFAULT_THRESHOLDS = {
    PatientMobilityLevel.NORMAL: {
        "shoulder_flexion_safe": 120, "shoulder_flexion_warning": 100,
        "shoulder_extension_safe": 60, "shoulder_extension_warning": 45,
        "shoulder_abduction_safe": 150, "shoulder_abduction_warning": 120,
        "elbow_flexion_safe": 150, "elbow_flexion_warning": 120,
        "elbow_extension_safe": 10, "elbow_extension_warning": 5,
        "wrist_flexion_safe": 80, "wrist_flexion_warning": 60,
        "wrist_extension_safe": 70, "wrist_extension_warning": 55
    },
    PatientMobilityLevel.LIMITED: {
        "shoulder_flexion_safe": 100, "shoulder_flexion_warning": 85,
        "shoulder_extension_safe": 45, "shoulder_extension_warning": 35,
        "shoulder_abduction_safe": 120, "shoulder_abduction_warning": 100,
        "elbow_flexion_safe": 130, "elbow_flexion_warning": 110,
        "elbow_extension_safe": 5, "elbow_extension_warning": 3,
        "wrist_flexion_safe": 70, "wrist_flexion_warning": 55,
        "wrist_extension_safe": 60, "wrist_extension_warning": 45
    },
    PatientMobilityLevel.RESTRICTED: {
        "shoulder_flexion_safe": 80, "shoulder_flexion_warning": 65,
        "shoulder_extension_safe": 35, "shoulder_extension_warning": 25,
        "shoulder_abduction_safe": 90, "shoulder_abduction_warning": 75,
        "elbow_flexion_safe": 110, "elbow_flexion_warning": 90,
        "elbow_extension_safe": 0, "elbow_extension_warning": 0,
        "wrist_flexion_safe": 60, "wrist_flexion_warning": 45,
        "wrist_extension_safe": 50, "wrist_extension_warning": 35
    },
    PatientMobilityLevel.POST_SURGICAL: {
        "shoulder_flexion_safe": 70, "shoulder_flexion_warning": 55,
        "shoulder_extension_safe": 30, "shoulder_extension_warning": 20,
        "shoulder_abduction_safe": 75, "shoulder_abduction_warning": 60,
        "elbow_flexion_safe": 100, "elbow_flexion_warning": 80,
        "elbow_extension_safe": 0, "elbow_extension_warning": 0,
        "wrist_flexion_safe": 50, "wrist_flexion_warning": 40,
        "wrist_extension_safe": 45, "wrist_extension_warning": 30
    },
    PatientMobilityLevel.REHABILITATION: {
        "shoulder_flexion_safe": 90, "shoulder_flexion_warning": 75,
        "shoulder_extension_safe": 40, "shoulder_extension_warning": 30,
        "shoulder_abduction_safe": 100, "shoulder_abduction_warning": 85,
        "elbow_flexion_safe": 120, "elbow_flexion_warning": 100,
        "elbow_extension_safe": 5, "elbow_extension_warning": 3,
        "wrist_flexion_safe": 65, "wrist_flexion_warning": 50,
        "wrist_extension_safe": 55, "wrist_extension_warning": 40
    }
}


class CalibrationWorkflow:
    """
    Guided calibration workflow for clinicians.
    
    Provides a step-by-step process to:
    1. Enter patient information
    2. Assess mobility level
    3. Measure range of motion
    4. Set personalized safety limits
    5. Validate calibration
    6. Save/load profiles
    """
    
    def __init__(self, calibration_dir: str = "calibrations"):
        """
        Initialize calibration workflow.
        
        Args:
            calibration_dir: Directory to store calibration profiles
        """
        self.calibration_dir = Path(calibration_dir)
        self.calibration_dir.mkdir(exist_ok=True)
        
        self.state = CalibrationState.NOT_STARTED
        self.current_profile: Optional[CalibrationProfile] = None
        self.step_responses: Dict[str, Any] = {}
    
    def start_calibration(
        self,
        patient_id: str,
        age: int,
        mobility_level: PatientMobilityLevel,
        injury_history: List[str] = None,
        surgery_type: str = None,
        surgery_date: str = None,
        therapist_notes: str = ""
    ) -> CalibrationProfile:
        """
        Start new calibration for a patient.
        
        Args:
            patient_id: Unique patient identifier
            age: Patient age
            mobility_level: Assessed mobility level
            injury_history: List of previous injuries
            surgery_type: Type of surgery if applicable
            surgery_date: Date of surgery if applicable
            therapist_notes: Clinical notes
            
        Returns:
            CalibrationProfile with default thresholds for mobility level
        """
        self.state = CalibrationState.PATIENT_INFO
        
        patient_info = PatientInfo(
            patient_id=patient_id,
            age=age,
            mobility_level=mobility_level,
            injury_history=injury_history or [],
            surgery_type=surgery_type,
            surgery_date=surgery_date,
            therapist_notes=therapist_notes
        )
        
        # Get default thresholds based on mobility level
        defaults = MOBILITY_DEFAULT_THRESHOLDS[mobility_level]
        
        self.current_profile = CalibrationProfile(
            profile_id=f"{patient_id}_{int(time.time())}",
            patient_info=patient_info,
            mobility_level=mobility_level,
            **defaults
        )
        
        self.step_responses["patient_info"] = patient_info.__dict__
        
        return self.current_profile
    
    def measure_rom(
        self,
        shoulder_flexion_rom: float,
        shoulder_extension_rom: float,
        shoulder_abduction_rom: float,
        elbow_flexion_rom: float,
        elbow_extension_rom: float,
        wrist_flexion_rom: float,
        wrist_extension_rom: float
    ) -> Dict[str, float]:
        """
        Record measured range of motion for patient.
        
        Args:
            Measured ROM values in degrees
            
        Returns:
            Dictionary of measured values
        """
        self.state = CalibrationState.RANGE_OF_MOTION
        
        rom_values = {
            "shoulder_flexion": shoulder_flexion_rom,
            "shoulder_extension": shoulder_extension_rom,
            "shoulder_abduction": shoulder_abduction_rom,
            "elbow_flexion": elbow_flexion_rom,
            "elbow_extension": elbow_extension_rom,
            "wrist_flexion": wrist_flexion_rom,
            "wrist_extension": wrist_extension_rom
        }
        
        self.step_responses["measured_rom"] = rom_values
        
        # Calculate recommended safety limits (70% of measured ROM)
        recommendations = {}
        for joint, value in rom_values.items():
            recommendations[f"{joint}_recommended_safe"] = round(value * 0.70, 1)
            recommendations[f"{joint}_recommended_warning"] = round(value * 0.60, 1)
        
        return recommendations
    
    def set_safety_limits(
        self,
        shoulder_flexion_safe: float = None,
        shoulder_flexion_warning: float = None,
        shoulder_extension_safe: float = None,
        shoulder_extension_warning: float = None,
        shoulder_abduction_safe: float = None,
        shoulder_abduction_warning: float = None,
        elbow_flexion_safe: float = None,
        elbow_flexion_warning: float = None,
        elbow_extension_safe: float = None,
        elbow_extension_warning: float = None,
        wrist_flexion_safe: float = None,
        wrist_flexion_warning: float = None,
        wrist_extension_safe: float = None,
        wrist_extension_warning: float = None,
        confidence_threshold: float = None
    ) -> CalibrationProfile:
        """
        Set personalized safety limits.
        
        Args:
            Safety limit values (use None to keep current values)
            
        Returns:
            Updated CalibrationProfile
        """
        if self.current_profile is None:
            raise ValueError("No calibration in progress. Call start_calibration first.")
        
        self.state = CalibrationState.SAFETY_LIMIT_SETTING
        
        # Update values that are provided
        updates = {
            "shoulder_flexion_safe": shoulder_flexion_safe,
            "shoulder_flexion_warning": shoulder_flexion_warning,
            "shoulder_extension_safe": shoulder_extension_safe,
            "shoulder_extension_warning": shoulder_extension_warning,
            "shoulder_abduction_safe": shoulder_abduction_safe,
            "shoulder_abduction_warning": shoulder_abduction_warning,
            "elbow_flexion_safe": elbow_flexion_safe,
            "elbow_flexion_warning": elbow_flexion_warning,
            "elbow_extension_safe": elbow_extension_safe,
            "elbow_extension_warning": elbow_extension_warning,
            "wrist_flexion_safe": wrist_flexion_safe,
            "wrist_flexion_warning": wrist_flexion_warning,
            "wrist_extension_safe": wrist_extension_safe,
            "wrist_extension_warning": wrist_extension_warning,
            "confidence_threshold": confidence_threshold
        }
        
        for key, value in updates.items():
            if value is not None:
                setattr(self.current_profile, key, value)
        
        self.step_responses["safety_limits"] = {
            k: v for k, v in updates.items() if v is not None
        }
        
        return self.current_profile
    
    def validate_calibration(
        self,
        therapist_name: str,
        validation_notes: str = ""
    ) -> bool:
        """
        Validate calibration before use.
        
        Args:
            therapist_name: Name of validating therapist
            validation_notes: Additional validation notes
            
        Returns:
            True if calibration is valid and approved
        """
        if self.current_profile is None:
            raise ValueError("No calibration in progress")
        
        self.state = CalibrationState.VALIDATION
        
        # Perform validation checks
        validation_passed = True
        validation_messages = []
        
        # Check that warning limits are below safe limits
        checks = [
            ("shoulder_flexion", self.current_profile.shoulder_flexion_warning,
             self.current_profile.shoulder_flexion_safe),
            ("shoulder_extension", self.current_profile.shoulder_extension_warning,
             self.current_profile.shoulder_extension_safe),
            ("shoulder_abduction", self.current_profile.shoulder_abduction_warning,
             self.current_profile.shoulder_abduction_warning),
            ("elbow_flexion", self.current_profile.elbow_flexion_warning,
             self.current_profile.elbow_flexion_safe),
            ("elbow_extension", self.current_profile.elbow_extension_warning,
             self.current_profile.elbow_extension_safe),
            ("wrist_flexion", self.current_profile.wrist_flexion_warning,
             self.current_profile.wrist_flexion_safe),
            ("wrist_extension", self.current_profile.wrist_extension_warning,
             self.current_profile.wrist_extension_safe),
        ]
        
        for joint, warning, safe in checks:
            if warning >= safe:
                validation_passed = False
                validation_messages.append(
                    f"{joint}: warning ({warning}°) must be less than safe ({safe}°)"
                )
        
        # Check confidence threshold is reasonable
        if not 0.3 <= self.current_profile.confidence_threshold <= 0.9:
            validation_passed = False
            validation_messages.append(
                f"Confidence threshold ({self.current_profile.confidence_threshold}) "
                "must be between 0.3 and 0.9"
            )
        
        self.current_profile.validation_passed = validation_passed
        self.current_profile.calibrated_by = therapist_name
        self.current_profile.notes = validation_notes
        self.current_profile.calibrated_at = time.time()
        
        if validation_passed:
            self.state = CalibrationState.COMPLETED
        
        self.step_responses["validation"] = {
            "passed": validation_passed,
            "messages": validation_messages,
            "validated_by": therapist_name,
            "notes": validation_notes
        }
        
        return validation_passed
    
    def save_profile(self, filepath: str = None) -> str:
        """
        Save calibration profile to file.
        
        Args:
            filepath: Optional filepath (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if self.current_profile is None:
            raise ValueError("No calibration to save")
        
        if filepath is None:
            filepath = self.calibration_dir / f"{self.current_profile.profile_id}.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.current_profile.to_dict(), f, indent=2)
        
        return str(filepath)
    
    def load_profile(self, filepath: str) -> CalibrationProfile:
        """
        Load calibration profile from file.
        
        Args:
            filepath: Path to calibration file
            
        Returns:
            Loaded CalibrationProfile
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.current_profile = CalibrationProfile.from_dict(data)
        self.state = CalibrationState.COMPLETED
        
        return self.current_profile
    
    def get_available_profiles(self) -> List[Dict]:
        """
        List all saved calibration profiles.
        
        Returns:
            List of profile summaries
        """
        profiles = []
        
        for filepath in self.calibration_dir.glob("*.json"):
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            profiles.append({
                "profile_id": data["profile_id"],
                "patient_id": data["patient_info"]["patient_id"],
                "mobility_level": data["mobility_level"],
                "calibrated_at": data.get("calibrated_at", 0),
                "validated": data.get("validation_passed", False),
                "filepath": str(filepath)
            })
        
        return profiles
    
    def get_config_for_safety_rules(self) -> Dict:
        """
        Get calibration as safety rules configuration.
        
        Returns:
            Dictionary suitable for SafetyRules initialization
        """
        if self.current_profile is None:
            raise ValueError("No calibration loaded")
        
        return self.current_profile.to_safety_rules_config()


def create_quick_calibration(
    patient_id: str,
    mobility_level: PatientMobilityLevel,
    therapist_name: str = ""
) -> CalibrationProfile:
    """
    Quick calibration with default thresholds for mobility level.
    
    Args:
        patient_id: Patient identifier
        mobility_level: Assessed mobility level
        therapist_name: Name of therapist
        
    Returns:
        Validated CalibrationProfile ready for use
    """
    workflow = CalibrationWorkflow()
    
    # Start with defaults
    profile = workflow.start_calibration(
        patient_id=patient_id,
        age=0,  # Not required for quick calibration
        mobility_level=mobility_level
    )
    
    # Validate with defaults
    workflow.validate_calibration(
        therapist_name=therapist_name,
        validation_notes="Quick calibration with default thresholds"
    )
    
    return workflow.current_profile


if __name__ == "__main__":
    # Example usage
    workflow = CalibrationWorkflow()
    
    # Quick calibration example
    profile = create_quick_calibration(
        patient_id="P001",
        mobility_level=PatientMobilityLevel.REHABILITATION,
        therapist_name="Dr. Smith"
    )
    
    print(f"Created calibration: {profile.profile_id}")
    print(f"Mobility level: {profile.mobility_level.value}")
    print(f"Shoulder flexion safe: {profile.shoulder_flexion_safe}°")
    print(f"Validation passed: {profile.validation_passed}")
    
    # Save profile
    saved_path = workflow.save_profile()
    print(f"Saved to: {saved_path}")
