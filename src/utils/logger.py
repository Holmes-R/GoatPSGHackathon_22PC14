import os
from datetime import datetime

class RobotLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_event(self, robot_id, action, path="", status="", battery=100, source_vertex=None, destination_vertex=None):
        """Universal logging method for all robot events"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        log_path = os.path.join(self.log_dir, f"robot_{robot_id}.log")
        
        log_entry_parts = [
            f"[{timestamp}] RobotID:{robot_id}",
            f"Action:{action.upper()}",
            f"Status:{status.upper()}",
            f"Battery:{battery}%"
        ]
        
        if path:
            log_entry_parts.append(f"Path:{path}")
        if source_vertex:
            log_entry_parts.append(f"From:{source_vertex}")
        if destination_vertex:
            log_entry_parts.append(f"To:{destination_vertex}")
        
        log_entry = " | ".join(log_entry_parts) + "\n"
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        return log_entry.strip()

robot_logger = RobotLogger()