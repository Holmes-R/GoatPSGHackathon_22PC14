import os
from datetime import datetime

class RobotLogger:
    def __init__(self, log_dir="src/logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_spawn(self, robot_id, source_vertex, destination_vertex=None, battery=100):
        """Log robot creation with vertex details"""
        log_path = os.path.join(self.log_dir, f"robot_{robot_id}.log")
        path = f"{source_vertex}->{destination_vertex}" if destination_vertex else source_vertex
        
        with open(log_path, 'w') as f:
            f.write(
                f"[{datetime.now()}] RobotID:{robot_id} | Action:SPAWN | "
                f"Path:{path} | Status:SUCCESS | Battery:{battery}%\n"
            )
        return log_path

    def log_action(self, robot_id, action, **kwargs):
        """Universal action logger (unchanged from previous)"""
        log_path = os.path.join(self.log_dir, f"robot_{robot_id}.log")
        log_parts = [
            f"[{datetime.now()}] RobotID:{robot_id}",
            f"Action:{action.upper()}"
        ]
        for key, value in kwargs.items():
            if value is not None:
                log_parts.append(f"{key.upper()}:{value}")
        
        with open(log_path, 'a') as f:
            f.write(" | ".join(log_parts) + "\n")

robot_logger = RobotLogger()