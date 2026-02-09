"""
PhysioSafe VR Safety System - Main Application
Real-time safety monitoring for physiotherapy exercises.

This is the "safety brain" that:
1. Tracks upper body movements via webcam
2. Calculates joint angles
3. Checks against safety thresholds
4. Outputs clean safety signals for VR systems
"""

import sys
import time
import json
import argparse
from datetime import datetime
from typing import Dict, Optional, Any

from angle_utils import AngleCalculator, Point3D
from safety_rules import SafetyRules, SafetyLevel
from signal_generator import NeuroSafeSignalEngine, SafetyFrameSignal
from pose_tracker import PoseTracker, MockPoseTracker, TrackingState


class PhysioSafeSystem:
    """
    Main safety system that coordinates all components.
    Provides real-time safety assessment for physiotherapy exercises.
    """
    
    def __init__(
        self,
        use_mock_tracker: bool = False,
        camera_index: int = 0,
        output_format: str = "json",
        verbose: bool = False,
        cooldown_enabled: bool = True,
        deduplication_enabled: bool = True
    ):
        """
        Initialize the PhysioSafe system.
        
        Args:
            use_mock_tracker: Use mock tracker instead of webcam
            camera_index: Webcam device index
            output_format: Output format (json, unreal, vr, minimal)
            verbose: Enable verbose output
            cooldown_enabled: Enable cooldown system
            deduplication_enabled: Enable signal deduplication
        """
        self.use_mock = use_mock_tracker
        self.output_format = output_format
        self.verbose = verbose
        
        # Initialize components
        self.safety_rules = SafetyRules()
        self.signal_engine = NeuroSafeSignalEngine(
            cooldown_enabled=cooldown_enabled,
            deduplication_enabled=deduplication_enabled
        )
        
        if use_mock_tracker:
            self.tracker = MockPoseTracker()
        else:
            self.tracker = PoseTracker(camera_index=camera_index)
        
        # State tracking
        self.is_running = False
        self.frame_count = 0
        self.start_time = 0
        self.assessments = []
        self.signals = []
        
        # Performance tracking
        self.processing_times = []
    
    def initialize(self) -> bool:
        """Initialize all components"""
        print("=" * 60)
        print("PhysioSafe VR Safety System - Neuro-Safe Engine")
        print("=" * 60)
        print(f"Version: 2.0.0")
        print(f"Mode: {'Mock Tracking' if self.use_mock else 'Webcam Tracking'}")
        print(f"Output Format: {self.output_format}")
        print(f"Cooldown: {'Enabled' if self.signal_engine.cooldown_enabled else 'Disabled'}")
        print(f"Deduplication: {'Enabled' if self.signal_engine.deduplication_enabled else 'Disabled'}")
        print("=" * 60)
        
        # Initialize tracker
        if not self.tracker.initialize():
            print("Error: Failed to initialize pose tracker")
            return False
        
        print("✓ System initialized successfully")
        print()
        
        return True
    
    def run(self, duration_seconds: Optional[float] = None):
        """
        Run the safety monitoring loop.
        
        Args:
            duration_seconds: Optional duration limit (None = infinite)
        """
        if not self.tracker.is_ready():
            print("Error: Tracker not ready")
            return
        
        self.is_running = True
        self.start_time = time.time()
        
        print("Starting safety monitoring...")
        print("-" * 60)
        
        try:
            while self.is_running:
                # Check duration limit
                if duration_seconds and (time.time() - self.start_time) > duration_seconds:
                    break
                
                # Process frame
                self._process_frame()
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        
        finally:
            self._shutdown()
    
    def _process_frame(self):
        """Process a single frame"""
        frame_start = time.time()
        
        # Update tracker
        success, landmarks, confidence = self.tracker.update()
        
        if not success or not landmarks:
            return
        
        # Extract angles
        angles = AngleCalculator.extract_angles(landmarks)
        
        if not angles:
            return
        
        # Calculate overall confidence
        overall_confidence = confidence.overall_confidence() if confidence else 0.5
        
        # Perform safety assessment
        assessment = self.safety_rules.assess_safety(
            angles=angles,
            confidence=overall_confidence,
            frame_number=self.frame_count,
            timestamp=time.time() - self.start_time
        )
        
        # Generate neuro-safe signal
        signal = self.signal_engine.process_frame(assessment, angles)
        
        # Output signal
        self._output_signal(signal)
        
        # Store for later analysis
        self.assessments.append(assessment)
        self.signals.append(signal)
        
        # Update frame count
        self.frame_count += 1
        
        # Track processing time
        processing_time = time.time() - frame_start
        self.processing_times.append(processing_time)
        
        # Verbose output
        if self.verbose and self.frame_count % 30 == 0:
            self._print_verbose(signal, assessment)
    
    def _output_signal(self, signal: SafetyFrameSignal):
        """Output signal in the specified format"""
        if self.output_format == "json":
            output = signal.to_json()
            print(output)
        elif self.output_format == "unreal":
            output = self.signal_engine._format_unreal(signal)
            print(json.dumps(output))
        elif self.output_format == "vr":
            output = self.signal_engine._format_vr(signal)
            print(json.dumps(output))
        elif self.output_format == "minimal":
            output = self.signal_engine._format_minimal(signal)
            print(json.dumps(output))
        else:
            # Default to JSON
            print(signal.to_json())
    
    def _print_verbose(self, signal: SafetyFrameSignal, assessment):
        """Print verbose information"""
        status_map = {
            "safe": "✓ SAFE",
            "warning": "⚠ WARNING",
            "danger": "✗ DANGER",
            "unknown": "? UNKNOWN"
        }
        
        status = status_map.get(signal.safety_flag, "?")
        fps = self.frame_count / (time.time() - self.start_time + 0.001)
        
        print(f"\n[Frame {signal.frame_number}] {status}")
        print(f"  Confidence: {signal.confidence:.1%}")
        print(f"  Severity: {signal.severity}/3")
        print(f"  Phase: {signal.phase}")
        print(f"  Violations: {signal.active_violations}")
        print(f"  FPS: {fps:.1f}")
        
        if signal.correction:
            print(f"  Correction: {signal.correction['instruction']}")
    
    def _shutdown(self):
        """Shutdown and cleanup"""
        self.is_running = False
        self.tracker.release()
        
        print("-" * 60)
        print("Session Summary")
        print("-" * 60)
        print(f"Total Frames: {self.frame_count}")
        print(f"Duration: {time.time() - self.start_time:.1f} seconds")
        
        if self.processing_times:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            avg_fps = 1.0 / avg_time if avg_time > 0 else 0
            print(f"Average FPS: {avg_fps:.1f}")
            print(f"Average Processing Time: {avg_time*1000:.1f}ms")
        
        # Signal statistics
        stats = self.signal_engine.get_statistics()
        print(f"\nSignal Statistics:")
        print(f"  Safe signals: {stats['safe']}")
        print(f"  Warning signals: {stats['warning']}")
        print(f"  Danger signals: {stats['danger']}")
        print(f"  Suppressed signals: {stats['suppressed']}")
        print(f"  Phase changes: {stats['phase_changes']}")
        
        print("\n✓ System shutdown complete")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "is_running": self.is_running,
            "frame_count": self.frame_count,
            "uptime": time.time() - self.start_time if self.is_running else 0,
            "tracker_state": self.tracker.state.value if hasattr(self.tracker.state, 'value') else str(self.tracker.state),
            "last_signal": self.signals[-1].to_dict() if self.signals else None,
            "output_format": self.output_format
        }
    
    def export_data(self, filepath: str):
        """Export assessment data to file"""
        data = {
            "session_info": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "frame_count": self.frame_count,
                "output_format": self.output_format
            },
            "signals": [s.to_dict() for s in self.signals],
            "statistics": self.signal_engine.get_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data exported to {filepath}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="PhysioSafe VR Safety System - Neuro-Safe Real-Time Signal Engine"
    )
    
    parser.add_argument(
        "--mock", "-m",
        action="store_true",
        help="Use mock tracking (no webcam required)"
    )
    parser.add_argument(
        "--camera", "-c",
        type=int,
        default=0,
        help="Camera device index (default: 0)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "unreal", "vr", "minimal"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=None,
        help="Duration in seconds (default: unlimited)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--no-cooldown",
        action="store_true",
        help="Disable cooldown system"
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable signal deduplication"
    )
    
    args = parser.parse_args()
    
    # Create and run system
    system = PhysioSafeSystem(
        use_mock_tracker=args.mock,
        camera_index=args.camera,
        output_format=args.format,
        verbose=args.verbose,
        cooldown_enabled=not args.no_cooldown,
        deduplication_enabled=not args.no_dedup
    )
    
    if system.initialize():
        system.run(duration_seconds=args.duration)


if __name__ == "__main__":
    main()
