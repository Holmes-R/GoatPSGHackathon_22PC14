import threading
from collections import defaultdict, deque
import time
from typing import Dict, List, Tuple, Optional
import heapq
from src.utils.helper import PathFinder

class TrafficManager:
    def __init__(self, fleet_manager=None):
        self.lane_occupancy = defaultdict(list)
        self.fleet_manager = fleet_manager
        self.reserved_lanes = {} 
        self.waiting_queues = defaultdict(deque) 
        self.congestion_data = defaultdict(float) 
        self.robot_timeouts = {} 
        self.lock = threading.Lock()
        self.priority_weights = defaultdict(float) 
        self.robot_destinations = {}
        self.lane_reservations = {}
        
    ### LANE AND PATH MANAGEMENT 
    def reserve_path(self, robot_id, path_indices):
        """Reserve all lanes in a path"""
        lanes = []
        for i in range(len(path_indices)-1):
            from_idx = path_indices[i]
            to_idx = path_indices[i+1]
            lanes.append((min(from_idx, to_idx), max(from_idx, to_idx)))
        
        for lane in lanes:
            if not self.reserve_lane(lane, robot_id):
                for reserved_lane in lanes:
                    if reserved_lane in self.lane_reservations:
                        self.release_lane(reserved_lane)
                return False
        return True

    def release_path(self, robot_id, path_indices):
        """Release all lanes in a path"""
        for i in range(len(path_indices)-1):
            from_idx = path_indices[i]
            to_idx = path_indices[i+1]
            lane = (min(from_idx, to_idx), max(from_idx, to_idx))
            self.release_lane(lane)

    def reserve_lane(self, lane, robot_id):
        """Reserve a lane for a specific robot"""
        if lane in self.lane_reservations:
            return False  
        self.lane_reservations[lane] = robot_id
        return True

    def release_lane(self, lane):
        """Release a reserved lane"""
        if lane in self.lane_reservations:
            del self.lane_reservations[lane]

    def release_all_for_robot(self, robot_id):
        """Release all lanes reserved by a specific robot"""
        lanes_to_release = [lane for lane, reserver in self.lane_reservations.items() 
                          if reserver == robot_id]
        for lane in lanes_to_release:
            self.release_lane(lane)

    def wait_for_lane(self, robot_id: str, lane: tuple, timeout=5.0):
        """Wait for a lane to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.reserve_lane(robot_id, lane):
                return True
            time.sleep(0.1)
        return False
        
    ### NAVIGATION AND PATHFINDING  

    def find_least_congested_path(self, nav_graph: Dict, start_idx: int, end_idx: int) -> List[int]:
        """
        Find the least congested path using A* algorithm with congestion-aware cost function.
        """
        def heuristic(u, v):
            p1 = nav_graph["vertices"][u]
            p2 = nav_graph["vertices"][v]
            return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
        
        def edge_cost(u, v):
            p1 = nav_graph["vertices"][u]
            p2 = nav_graph["vertices"][v]
            base_cost = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
            congestion = self.congestion_data.get((u, v), 0)
            return base_cost * (1 + congestion * 2)
        
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
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            
            neighbors = set()
            for lane in nav_graph["lanes"]:
                if lane[0] == current:
                    neighbors.add(lane[1])
                elif lane[1] == current:  
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
        
        return []
    
    def find_path(self, start_idx: int, end_idx: int) -> List[int]:
        """Uses the PathFinder helper with congestion data"""
        return PathFinder.find_path(
            self.nav_graph,
            start_idx,
            end_idx,
            self.congestion_data
        )
    
    def _path_to_lanes(self, path_indices: List[int]) -> List[Tuple[int, int]]:
        """Convert path indices to lane tuples."""
        if not path_indices or len(path_indices) < 2:
            return []
        return [(path_indices[i], path_indices[i+1]) for i in range(len(path_indices)-1)]
    
    ### TRAFFIC AND CONGESTION HANDLING 

    def _update_congestion(self, lane: Tuple[int, int]):
        """Update congestion data for the lane."""
        self.congestion_data[lane] = 0.9 * self.congestion_data.get(lane, 0) + 0.1

    def get_lane_status(self, lane: Tuple[int, int]) -> str:
        """Enhanced lane status with automatic updates"""
        with self.lock:
            if lane not in self.reserved_lanes:
                return "green"
            elif self.waiting_queues[lane]:
                return "red"
            else:
                return "yellow"
    
    def _distance(self, p1: tuple, p2: tuple) -> float:
        """Calculate Euclidean distance between two points"""
        return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
    ### CONGESTION DETECTION AND ROBOT PRIORITY 

    # In TrafficManager class
    def detect_collision(self, robot_positions: Dict[str, Tuple[float, float]], threshold: float = 2.0) -> List[Tuple[str, str]]:
        """Optimized collision detection using spatial hashing"""
        grid_size = threshold * 2
        spatial_grid = defaultdict(list)
        
        # Bin robots into grid cells
        for robot_id, pos in robot_positions.items():
            grid_x = int(pos[0] / grid_size)
            grid_y = int(pos[1] / grid_size)
            spatial_grid[(grid_x, grid_y)].append((robot_id, pos))
        
        collisions = []
        # Only check robots in same or adjacent cells
        for (grid_x, grid_y), robots in spatial_grid.items():
            # Check within cell
            for i in range(len(robots)):
                id1, pos1 = robots[i]
                for j in range(i+1, len(robots)):
                    id2, pos2 = robots[j]
                    if self._distance(pos1, pos2) < threshold:
                        collisions.append((id1, id2))
            
            # Check adjacent cells
            for dx, dy in [(1,0), (0,1), (1,1), (-1,1)]:
                neighbor_key = (grid_x + dx, grid_y + dy)
                if neighbor_key in spatial_grid:
                    for (id1, pos1) in robots:
                        for (id2, pos2) in spatial_grid[neighbor_key]:
                            if self._distance(pos1, pos2) < threshold:
                                collisions.append((id1, id2))
        
        return collisions
    
    def negotiate_priority(self, robot1: str, robot2: str) -> str:
        """
        Negotiate priority between two robots.
        Returns the robot_id that should go first.
        """
        with self.lock:
            if self.priority_weights[robot1] >= self.priority_weights[robot2]:
                return robot1
            return robot2
    
    def set_robot_priority(self, robot_id: str, priority: float):
        """Set priority weight for a robot."""
        with self.lock:
            self.priority_weights[robot_id] = priority

    ### UTILITY FUNCTION 
    
    def get_robot_by_id(self, robot_id):
        """Public method to access robots"""
        return next((r for r in self.robots if r.robot_id == robot_id), None)

    def has_reached_destination(self, current_pos, target_pos):
        """Public destination check"""
        return self._has_reached_destination(current_pos, target_pos)
    
    def release_all_for_robot(self, robot_id):
        """Release all reservations for a specific robot"""
        lanes_to_release = [lane for lane, reserved_by in self.lane_reservations.items() 
                        if reserved_by == robot_id]
        for lane in lanes_to_release:
            self.release_lane(lane)

    def _check_robot_timeout(self, robot_id: str) -> bool:
        """Check if robot's wait timeout has expired."""
        return time.time() < self.robot_timeouts.get(robot_id, float('inf'))
    
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
            
            self.waiting_queues[lane].append(robot_id)
            self.robot_timeouts[robot_id] = time.time() + timeout_sec
            return False
    