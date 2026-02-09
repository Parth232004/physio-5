#!/usr/bin/env python3
"""
PhysioSafe VR Safety System - Demo Script

10-15 minute continuous run with:
- Timestamped logging of signals + safety events
- Webcam + console recording
- Session export for analysis

Usage:
    python run_demo.py --duration 900          # 15 minutes
    python run_demo.py --mock --duration 60    # 1 minute mock test
    python run_demo.py --webcam --duration 300  # 5 minutes with webcam
"""

import sys
import time
import json
import argparse
import os
from datetime import datetime
from typing import Optional

# Import PhysioSafe modules
from main import PhysioSafeSystem
from session_logger import SessionLogger, LogLevel, create_demo_logger
from signal_generator import NeuroSafeSignalEngine


class DemoRunner:
    """
    Demo runner for PhysioSafe VR Safety System.
    
    Features:
    - Configurable duration
    - Session logging
    - Progress reporting
    - Session export
    """
    
    def __init__(
        self,
        duration_seconds: int = 900,  # 15 minutes default
        use_mock: bool = False,
        camera_index: int = 0,
        output_format: str = "json",
        session_id: Optional[str] = None,
        log_dir: str = "logs"
    ):
        """
        Initialize demo runner.
        
        Args:
            duration_seconds: Demo duration in seconds
            use_mock: Use mock tracker
            camera_index: Webcam index
            output_format: Output format
            session_id: Session identifier
            log_dir: Log directory
        """
        self.duration_seconds = duration_seconds
        self.use_mock = use_mock
        self.camera_index = camera_index
        self.output_format = output_format
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = log_dir
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = SessionLogger(
            log_file=f"{log_dir}/{self.session_id}_signals.jsonl",
            safety_events_file=f"{log_dir}/{self.session_id}_events.json",
            console_output=True,
            min_log_level=LogLevel.INFO
        )
        
        # Initialize system
        self.system = PhysioSafeSystem(
            use_mock_tracker=use_mock,
            camera_index=camera_index,
            output_format=output_format,
            verbose=False,
            cooldown_enabled=True,
            deduplication_enabled=True
        )
        
        # State
        self.start_time = 0
        self.running = False
    
    def run(self):
        """Run the demo"""
        print("=" * 70)
        print("PhysioSafe VR Safety System - Demo Mode")
        print("=" * 70)
        print(f"Session ID: {self.session_id}")
        print(f"Duration: {self.duration_seconds} seconds ({self.duration_seconds/60:.1f} minutes)")
        print(f"Mode: {'Mock Tracking' if self.use_mock else 'Webcam Tracking'}")
        print(f"Output: {self.output_format}")
        print(f"Log Directory: {self.log_dir}")
        print("=" * 70)
        
        # Initialize system
        if not self.system.initialize():
            self.logger.log(
                message="Failed to initialize system",
                category="error",
                level=LogLevel.ERROR
            )
            return False
        
        self.logger.log(
            message=f"Demo started - Duration: {self.duration_seconds}s",
            category="demo",
            level=LogLevel.INFO
        )
        
        self.running = True
        self.start_time = time.time()
        
        try:
            # Run for specified duration
            while self.running:
                elapsed = time.time() - self.start_time
                
                # Check duration
                if elapsed >= self.duration_seconds:
                    self.logger.log(
                        message=f"Demo duration reached ({self.duration_seconds}s)",
                        category="demo",
                        level=LogLevel.INFO
                    )
                    break
                
                # Process frame
                self._process_frame()
                
                # Progress update every 30 seconds
                if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                    self._report_progress(elapsed)
        
        except KeyboardInterrupt:
            self.logger.log(
                message="Demo interrupted by user",
                category="demo",
                level=LogLevel.WARNING
            )
        except Exception as e:
            self.logger.log(
                message=f"Demo error: {str(e)}",
                category="error",
                level=LogLevel.ERROR
            )
            raise
        
        finally:
            self._shutdown()
        
        return True
    
    def _process_frame(self):
        """Process a single frame with logging"""
        frame_start = time.time()
        
        # Get current frame from system
        if len(self.system.signals) > 0:
            last_signal = self.system.signals[-1]
            
            # Log signal
            self.logger.log_signal(
                signal_data=last_signal.to_dict(),
                frame_number=last_signal.frame_number
            )
            
            # Log safety events
            if last_signal.safety_flag == "danger":
                self.logger.log_safety_event(
                    event_type="danger",
                    description=f"Danger signal - {last_signal.primary_violation or 'unknown'}",
                    severity=3,
                    frame_number=last_signal.frame_number,
                    signal_data=last_signal.to_dict()
                )
            elif last_signal.safety_flag == "warning":
                self.logger.log_safety_event(
                    event_type="warning",
                    description=f"Warning signal - {last_signal.primary_violation or 'unknown'}",
                    severity=2,
                    frame_number=last_signal.frame_number,
                    signal_data=last_signal.to_dict()
                )
            
            # Log corrections
            if last_signal.correction and last_signal.is_new:
                self.logger.log_correction(
                    joint=last_signal.correction.get("joint", ""),
                    direction=last_signal.correction.get("direction", ""),
                    target=last_signal.correction.get("target_angle", 0),
                    frame_number=last_signal.frame_number
                )
        
        # Update system (runs one frame)
        self.system._process_frame()
    
    def _report_progress(self, elapsed: float):
        """Report demo progress"""
        frames = self.system.frame_count
        fps = frames / elapsed if elapsed > 0 else 0
        remaining = self.duration_seconds - elapsed
        
        stats = self.logger.get_statistics()
        
        print(f"\n{'='*50}")
        print(f"PROGRESS REPORT - {elapsed:.0f}s / {self.duration_seconds}s")
        print(f"{'='*50}")
        print(f"Frames Processed: {frames}")
        print(f"Current FPS: {fps:.1f}")
        print(f"Time Remaining: {remaining:.0f}s")
        print(f"Log Entries: {stats['total_entries']}")
        print(f"Safety Events: {stats['safety_events']}")
        print(f"{'='*50}\n")
        
        self.logger.log(
            message=f"Progress: {elapsed:.0f}s / {self.duration_seconds}s ({100*elapsed/self.duration_seconds:.1f}%)",
            category="progress",
            level=LogLevel.INFO,
            data={
                "frames": frames,
                "fps": round(fps, 1),
                "remaining_seconds": round(remaining, 0)
            }
        )
    
    def _shutdown(self):
        """Shutdown demo and export session"""
        self.running = False
        self.system._shutdown()
        
        # Get final statistics
        elapsed = time.time() - self.start_time
        stats = self.logger.get_statistics()
        
        # Export session
        session_file = f"{self.log_dir}/{self.session_id}_session.json"
        self.logger.export_session(session_file)
        
        # Print summary
        print("\n" + "=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        print(f"Session ID: {self.session_id}")
        print(f"Total Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"Frames Processed: {self.system.frame_count}")
        print(f"Average FPS: {self.system.frame_count / elapsed:.1f}" if elapsed > 0 else "N/A")
        print(f"Log Entries: {stats['total_entries']}")
        print(f"Safety Events: {stats['safety_events']}")
        print(f"\nOutput Files:")
        print(f"  - {self.log_dir}/{self.session_id}_signals.jsonl")
        print(f"  - {self.log_dir}/{self.session_id}_events.json")
        print(f"  - {session_file}")
        print("=" * 70)
        
        self.logger.log(
            message=f"Demo complete - {elapsed:.1f}s, {self.system.frame_count} frames",
            category="demo",
            level=LogLevel.INFO,
            data={
                "duration_seconds": round(elapsed, 1),
                "frames": self.system.frame_count,
                "fps": round(self.system.frame_count / elapsed, 1) if elapsed > 0 else 0
            }
        )
        
        self.logger.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="PhysioSafe VR Safety System - Demo Runner"
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=900,
        help="Demo duration in seconds (default: 900 = 15 minutes)"
    )
    parser.add_argument(
        "--mock", "-m",
        action="store_true",
        help="Use mock tracking instead of webcam"
    )
    parser.add_argument(
        "--webcam", "-w",
        action="store_true",
        help="Use webcam (default: uses webcam if available)"
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
        "--session", "-s",
        type=str,
        default=None,
        help="Session ID (auto-generated if not specified)"
    )
    parser.add_argument(
        "--log-dir", "-l",
        type=str,
        default="logs",
        help="Log directory (default: logs)"
    )
    parser.add_argument(
        "--quick-test", "-q",
        action="store_true",
        help="Quick 60-second test"
    )
    
    args = parser.parse_args()
    
    # Handle quick test
    if args.quick_test:
        args.duration = 60
        args.mock = True
    
    # Determine tracking mode
    use_mock = args.mock or not args.webcam
    
    # Create and run demo
    runner = DemoRunner(
        duration_seconds=args.duration,
        use_mock=use_mock,
        camera_index=args.camera,
        output_format=args.format,
        session_id=args.session,
        log_dir=args.log_dir
    )
    
    success = runner.run()
    
    if success:
        print("\n✅ Demo completed successfully!")
        print("Check the log files for detailed session data.")
    else:
        print("\n❌ Demo failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
