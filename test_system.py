"""
Test script for PhysioSafe VR Safety System.
Validates all components including the neuro-safe signal engine.
"""

import sys
import time
from angle_utils import Point3D, AngleCalculator
from safety_rules import SafetyRules, SafetyLevel, SafetyAssessment
from signal_generator import (
    NeuroSafeSignalEngine, 
    SafetyFrameSignal, 
    ExercisePhase, 
    Severity,
    CorrectionGuidance
)
from pose_tracker import MockPoseTracker, TrackingConfidence


def test_angle_calculator():
    """Test angle calculation functions"""
    print("Testing Angle Calculator...")
    
    # Test points forming a 90-degree angle
    p1 = Point3D(0, 1, 0)
    p2 = Point3D(0, 0, 0)
    p3 = Point3D(1, 0, 0)
    
    angle = AngleCalculator.calculate_angle(p1, p2, p3)
    assert 89 < angle < 91, f"Expected ~90°, got {angle}"
    
    # Test shoulder flexion calculation
    shoulder = Point3D(0, 0, 0)
    elbow = Point3D(0.5, 0, 0)
    wrist = Point3D(1, 0, 0)
    
    flexion = AngleCalculator.calculate_shoulder_flexion(shoulder, elbow, wrist)
    assert flexion < 5, f"Expected near 0° (straight arm), got {flexion}"
    
    # Test 90-degree elbow
    elbow2 = Point3D(0, 0.5, 0)
    elbow_flexion = AngleCalculator.calculate_elbow_flexion(shoulder, elbow2, wrist)
    assert 88 < elbow_flexion < 92, f"Expected ~90°, got {elbow_flexion}"
    
    print("✓ Angle Calculator tests passed")


def test_safety_rules():
    """Test safety rules engine"""
    print("Testing Safety Rules...")
    
    rules = SafetyRules()
    
    # Test safe angle
    level, message = rules.check_angle("shoulder_left", "flexion", 90)
    assert level == SafetyLevel.SAFE, f"Expected SAFE for 90°, got {level}"
    
    # Test warning angle
    level, message = rules.check_angle("shoulder_left", "flexion", 110)
    assert level == SafetyLevel.WARNING, f"Expected WARNING for 110°, got {level}"
    
    # Test danger angle
    level, message = rules.check_angle("shoulder_left", "flexion", 130)
    assert level == SafetyLevel.DANGER, f"Expected DANGER for 130°, got {level}"
    
    print("✓ Safety Rules tests passed")


def test_neuro_safe_engine():
    """Test the neuro-safe signal engine"""
    print("Testing Neuro-Safe Signal Engine...")
    
    # Test initialization
    engine = NeuroSafeSignalEngine(cooldown_enabled=True, deduplication_enabled=True)
    assert engine is not None, "Engine should initialize"
    
    # Test with safe assessment
    safe_assessment = SafetyAssessment(
        overall_safety=SafetyLevel.SAFE,
        is_safe=True,
        confidence=0.92,
        violations=[],
        signals={"action_type": "continue", "urgency_level": 0},
        timestamp=time.time(),
        frame_number=1
    )
    
    signal = engine.process_frame(safe_assessment)
    assert isinstance(signal, SafetyFrameSignal), "Should return SafetyFrameSignal"
    assert signal.safety_flag == "safe", f"Expected safe, got {signal.safety_flag}"
    assert signal.confidence == 0.92, f"Expected 0.92, got {signal.confidence}"
    assert signal.severity == Severity.INFO.value, f"Expected INFO severity"
    assert signal.correction is None, "Safe signal should have no correction"
    assert signal.is_new == True, "First signal should be new"
    
    # Test with warning assessment
    warning_assessment = SafetyAssessment(
        overall_safety=SafetyLevel.WARNING,
        is_safe=True,
        confidence=0.85,
        violations=[
            type('Violation', (), {
                'joint': 'shoulder_left',
                'movement': 'flexion',
                'current_angle': 115.0,
                'safe_limit': 120.0,
                'safety_level': SafetyLevel.WARNING,
                'message': 'Shoulder flexion approaching limit'
            })()
        ],
        signals={"action_type": "correct_position", "urgency_level": 2},
        timestamp=time.time() + 0.1,
        frame_number=2
    )
    
    signal = engine.process_frame(warning_assessment)
    assert signal.safety_flag == "warning", f"Expected warning, got {signal.safety_flag}"
    assert signal.severity == Severity.MEDIUM.value, f"Expected MEDIUM severity"
    assert signal.correction is not None, "Warning signal should have correction"
    assert signal.active_violations == 1, f"Expected 1 violation, got {signal.active_violations}"
    
    # Test deduplication (same signal code)
    signal2 = engine.process_frame(warning_assessment)
    assert signal2.is_new == False, "Duplicate signal should be suppressed"
    
    # Test with danger assessment
    danger_assessment = SafetyAssessment(
        overall_safety=SafetyLevel.DANGER,
        is_safe=False,
        confidence=0.95,
        violations=[
            type('Violation', (), {
                'joint': 'elbow_right',
                'movement': 'extension',
                'current_angle': -10.0,
                'safe_limit': -5.0,
                'safety_level': SafetyLevel.DANGER,
                'message': 'Elbow hyperextension detected'
            })()
        ],
        signals={"action_type": "stop_immediately", "urgency_level": 3},
        timestamp=time.time() + 0.2,
        frame_number=3
    )
    
    signal = engine.process_frame(danger_assessment)
    assert signal.safety_flag == "danger", f"Expected danger, got {signal.safety_flag}"
    assert signal.severity == Severity.HIGH.value, f"Expected HIGH severity"
    assert signal.correction is not None, "Danger signal should have correction"
    
    # Test phase detection
    assert signal.phase in [e.value for e in ExercisePhase], f"Invalid phase: {signal.phase}"
    
    # Test statistics
    stats = engine.get_statistics()
    assert stats['total_frames'] == 4, f"Expected 4 frames, got {stats['total_frames']}"
    assert stats['safe'] == 1, f"Expected 1 safe signal, got {stats['safe']}"
    assert stats['warning'] == 2, f"Expected 2 warning signals, got {stats['warning']}"
    assert stats['danger'] == 1, f"Expected 1 danger signal, got {stats['danger']}"
    assert stats['suppressed'] == 1, f"Expected 1 suppressed signal, got {stats['suppressed']}"
    
    print("✓ Neuro-Safe Signal Engine tests passed")


def test_output_formats():
    """Test different output formats"""
    print("Testing Output Formats...")
    
    engine = NeuroSafeSignalEngine()
    
    # Create test signal
    signal = SafetyFrameSignal(
        frame_number=100,
        timestamp=5.4321,
        safety_flag="warning",
        confidence=0.87,
        severity=2,
        phase="active",
        correction=CorrectionGuidance(
            joint="shoulder_left",
            movement="flexion",
            direction="lower",
            target_angle=120.0,
            instruction="Reduce shoulder flexion angle"
        ),
        is_new=True,
        signal_code="warning_shoulder_flexion_high_conf_active",
        active_violations=1,
        primary_violation="shoulder_left flexion"
    )
    
    # Test JSON format
    json_output = signal.to_dict()
    assert "frame" in json_output
    assert "safety_flag" in json_output
    assert "confidence" in json_output
    assert "severity" in json_output
    assert "phase" in json_output
    assert "correction" in json_output
    
    # Test Unreal format
    unreal_output = engine._format_unreal(signal)
    assert "safety_flag" in unreal_output
    assert "action_required" in unreal_output
    assert "command_code" in unreal_output
    assert unreal_output["action_required"] == True
    
    # Test VR format
    vr_output = engine._format_vr(signal)
    assert "haptic_intensity" in vr_output
    assert "audio_cue" in vr_output
    assert "visual_color" in vr_output
    
    # Test minimal format
    minimal_output = engine._format_minimal(signal)
    assert "s" in minimal_output  # safety_flag first letter
    assert "c" in minimal_output  # confidence
    assert "v" in minimal_output  # severity
    assert "p" in minimal_output  # phase first letter
    assert "n" in minimal_output  # is_new
    assert minimal_output["s"] == "W"  # Warning
    assert minimal_output["v"] == 2     # Medium severity
    
    print("✓ Output Formats tests passed")


def test_phase_detection():
    """Test exercise phase detection"""
    print("Testing Phase Detection...")
    
    engine = NeuroSafeSignalEngine()
    
    # Test REST phase
    rest_assessment = SafetyAssessment(
        overall_safety=SafetyLevel.SAFE,
        is_safe=True,
        confidence=0.95,
        violations=[],
        signals={},
        timestamp=0,
        frame_number=0
    )
    
    signal = engine.process_frame(rest_assessment)
    assert signal.phase == "rest", f"Expected rest phase, got {signal.phase}"
    
    # Test with movement (active phase)
    active_assessment = SafetyAssessment(
        overall_safety=SafetyLevel.SAFE,
        is_safe=True,
        confidence=0.92,
        violations=[],
        signals={},
        timestamp=1.0,
        frame_number=1
    )
    
    angles = {"left_shoulder_flexion": 45.0}
    signal = engine.process_frame(active_assessment, angles)
    assert signal.phase == "active", f"Expected active phase, got {signal.phase}"
    
    print("✓ Phase Detection tests passed")


def test_cooldown_system():
    """Test cooldown functionality"""
    print("Testing Cooldown System...")
    
    engine = NeuroSafeSignalEngine(cooldown_enabled=True, deduplication_enabled=False)
    
    # Create warning assessment
    warning_assessment = SafetyAssessment(
        overall_safety=SafetyLevel.WARNING,
        is_safe=True,
        confidence=0.9,
        violations=[],
        signals={},
        timestamp=0,
        frame_number=0
    )
    
    # First signal should emit
    signal1 = engine.process_frame(warning_assessment)
    assert signal1.is_new == True, "First warning should emit"
    
    # Immediate second signal should be suppressed by cooldown
    signal2 = engine.process_frame(warning_assessment)
    assert signal2.is_new == False, "Second signal should be suppressed by cooldown"
    
    print("✓ Cooldown System tests passed")


def test_full_system():
    """Test complete system integration"""
    print("Testing Full System Integration...")
    
    from main import PhysioSafeSystem
    
    # Create system with mock tracker
    system = PhysioSafeSystem(
        use_mock_tracker=True, 
        output_format="json",
        cooldown_enabled=True,
        deduplication_enabled=True
    )
    assert system.initialize(), "System should initialize"
    
    # Run for a short time
    system.run(duration_seconds=3)
    
    assert system.frame_count > 0, "Should process frames"
    assert len(system.signals) > 0, "Should generate signals"
    
    # Check signals have required fields
    for signal in system.signals:
        assert hasattr(signal, 'safety_flag')
        assert hasattr(signal, 'confidence')
        assert hasattr(signal, 'severity')
        assert hasattr(signal, 'phase')
        assert hasattr(signal, 'correction')
        assert hasattr(signal, 'is_new')
    
    # Check last signal
    last = system.signals[-1]
    assert last.safety_flag in ["safe", "warning", "danger", "unknown"]
    
    print("✓ Full System Integration test passed")


def main():
    """Run all tests"""
    print("=" * 60)
    print("PhysioSafe VR Safety System - Neuro-Safe Engine Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Angle Calculator", test_angle_calculator),
        ("Safety Rules", test_safety_rules),
        ("Neuro-Safe Signal Engine", test_neuro_safe_engine),
        ("Output Formats", test_output_formats),
        ("Phase Detection", test_phase_detection),
        ("Cooldown System", test_cooldown_system),
        ("Full System Integration", test_full_system),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[Running] {name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
