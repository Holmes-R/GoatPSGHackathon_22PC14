# traffic_manager.py
import threading
from collections import defaultdict, deque
import time
from typing import Dict, List, Tuple, Optional
import heapq
from src.utils.helper import PathFinder

class TrafficManager:
    def __init__(self):
        self.lane_occupancy = defaultdict(list)  # {lane: [robot_ids]}
        self.reserved_lanes = {}  # {lane: robot_id}
        self.waiting_queues = defaultdict(deque)  # {lane: deque(robot_ids)}
        self.congestion_data = defaultdict(float)  # {lane: congestion_score}
        self.robot_timeouts = {}  # {robot_id: timeout_timestamp}
        self.lock = threading.Lock()
        self.priority_weights = defaultdict(float)  # {robot_id: priority_weight}
        
    def reserve_path(self, robot_id: str, path_indices: List[int]) -> bool:
        """
        Attempt to reserve all lanes in a path atomically.
        Returns True if successful, False otherwise.
        """
        lanes = self._path_to_lanes(path_indices)
        
        # First check if all lanes are available
        with self.lock:
            for lane in lanes:
                if lane in self.reserved_lanes and self.reserved_lanes[lane] != robot_id:
                    return False
        
        # If all available, reserve them
        with self.lock:
            for lane in lanes:
                self.reserved_lanes[lane] = robot_id
                self._update_congestion(lane)
            return True
    
    def try_reserve_lane(self, robot_id: str, lane: Tuple[int, int], timeout_sec: float = 5.0) -> bool:
        """
        Attempt to reserve a single lane with timeout.
        Returns True if successful, False otherwise.
        """
        with self.lock:
            if lane not in self.reserved_lanes:
                self.reserved_lanes[lane] = robot_id
                self._update_congestion(lane)
                return True
            
            # Add to waiting queue if lane is occupied
            self.waiting_queues[lane].append(robot_id)
            self.robot_timeouts[robot_id] = time.time() + timeout_sec
            return False
    
    def release_path(self, robot_id: str, path_indices: List[int]):
        """
        Release all lanes in a path and notify next robots in queue.
        """
        lanes = self._path_to_lanes(path_indices)
        with self.lock:
            for lane in lanes:
                if self.reserved_lanes.get(lane) == robot_id:
                    del self.reserved_lanes[lane]
                    
                    # Notify next robot in queue if available
                    if self.waiting_queues[lane]:
                        next_robot = self.waiting_queues[lane].popleft()
                        if self._check_robot_timeout(next_robot):
                            self.reserved_lanes[lane] = next_robot
    
    def _path_to_lanes(self, path_indices: List[int]) -> List[Tuple[int, int]]:
        """Convert path indices to lane tuples."""
        if not path_indices or len(path_indices) < 2:
            return []
        return [(path_indices[i], path_indices[i+1]) for i in range(len(path_indices)-1)]
    
    def _update_congestion(self, lane: Tuple[int, int]):
        """Update congestion data for the lane."""
        self.congestion_data[lane] = 0.9 * self.congestion_data.get(lane, 0) + 0.1
    
    def _check_robot_timeout(self, robot_id: str) -> bool:
        """Check if robot's wait timeout has expired."""
        return time.time() < self.robot_timeouts.get(robot_id, float('inf'))
    
    def get_lane_status(self, lane: Tuple[int, int]) -> str:
        """
        Get traffic light status for visualization.
        Returns "green" if available, "yellow" if reserved but no queue, "red" if reserved with queue.
        """
        with self.lock:
            if lane not in self.reserved_lanes:

                return "green"
            return "yellow" if not self.waiting_queues[lane] else "red"
    
    def find_least_congested_path(self, nav_graph: Dict, start_idx: int, end_idx: int) -> List[int]:
        """
        Find the least congested path using A* algorithm with congestion-aware cost function.
        """
        def heuristic(u, v):
            # Euclidean distance heuristic
            p1 = nav_graph["vertices"][u]
            p2 = nav_graph["vertices"][v]
            return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
        
        def edge_cost(u, v):
            # Base cost is distance, multiplied by congestion factor
            p1 = nav_graph["vertices"][u]
            p2 = nav_graph["vertices"][v]
            base_cost = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
            congestion = self.congestion_data.get((u, v), 0)
            return base_cost * (1 + congestion * 2)
        
        # A* algorithm implementation
        open_set = []
        heapq.heappush(open_set, (0, start_idx))
        
        came_from = {}
        g_score = {start_idx: 0}
        f_score = {start_idx: heuristic(start_idx, end_idx)}
        
        open_set_hash = {start_idx}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)
            
            if current == end_idx:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            
            # Get neighbors
            neighbors = set()
            for lane in nav_graph["lanes"]:
                if lane[0] == current:
                    neighbors.add(lane[1])
                elif lane[1] == current:  # Undirected graph
                    neighbors.add(lane[0])
            
            for neighbor in neighbors:
                tentative_g_score = g_score[current] + edge_cost(current, neighbor)
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, end_idx)
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        return []  # No path found
    
    def negotiate_priority(self, robot1: str, robot2: str) -> str:
        """
        Negotiate priority between two robots.
        Returns the robot_id that should go first.
        """
        with self.lock:
            # Simple priority based on weight (could be expanded with more complex logic)
            if self.priority_weights[robot1] >= self.priority_weights[robot2]:
                return robot1
            return robot2
    
    def set_robot_priority(self, robot_id: str, priority: float):
        """Set priority weight for a robot."""
        with self.lock:
            self.priority_weights[robot_id] = priority
    
    def detect_collision(self, robot_positions: Dict[str, Tuple[float, float]], threshold: float = 2.0) -> List[Tuple[str, str]]:
        """
        Detect potential collisions between robots.
        Returns list of robot pairs that are too close.
        """
        collisions = []
        robots = list(robot_positions.items())
        
        for i in range(len(robots)):
            id1, pos1 = robots[i]
            for j in range(i+1, len(robots)):
                id2, pos2 = robots[j]
                distance = ((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)**0.5
                if distance < threshold:
                    collisions.append((id1, id2))
        
        return collisions
    
    # Remove the old find_least_congested_path method and add:

    
    def find_path(self, start_idx: int, end_idx: int) -> List[int]:
        """Uses the PathFinder helper with congestion data"""
        return PathFinder.find_path(
            self.nav_graph,
            start_idx,
            end_idx,
            self.congestion_data
        )