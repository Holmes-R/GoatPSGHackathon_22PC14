from collections import defaultdict, deque
import threading
from typing import Optional, Tuple, Dict

class TaskManager:
    def __init__(self):
        self.task_queue: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
    
    def add_task(self, robot_id: str, destination: Tuple[float, float]) -> bool:
        """Add a new task to the queue"""
        with self.lock:
            self.task_queue[robot_id].append(destination)
            return True
    
    def get_next_task(self, robot_id: str) -> Optional[Tuple[float, float]]:
        """Get the next pending task"""
        with self.lock:
            return self.task_queue[robot_id].popleft() if self.task_queue[robot_id] else None
    
    def has_pending_tasks(self, robot_id: str) -> bool:
        """Check for pending tasks"""
        with self.lock:
            return bool(self.task_queue[robot_id])