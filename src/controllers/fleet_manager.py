import json
import random
from typing import Dict, List, Optional, Tuple
from src.models.robots import Robot
import time
from collections import deque
import threading
from collections import defaultdict
from src.controllers.traffic_manager import TrafficManager
from src.utils.helper import PathFinder
import math
import tkinter as tk
class FleetManager:
    def __init__(self):
        self.robots: List[Robot] = []
        self.robot_counter: int = 0
        self.vertex_colors: Dict[int, str] = {}
        self.vertex_names: Dict[int, str] = {}
        self.nav_graph: Optional[dict] = None
        self.robot_destinations: Dict[str, tuple] = {}
        self.selected_robot: Optional[Robot] = None
        self.navigation_delay = 2.0  # seconds between steps
        self.navigation_steps = 10
        self.traffic_manager = TrafficManager(self)        

        # Visualization states
        self.lane_status = {}
        
        # Visualization parameters
        self.padding: int = 50
        self.vertex_radius: int = 15
        self.min_x: float = 0
        self.max_x: float = 0
        self.min_y: float = 0
        self.max_y: float = 0
        self.scale_x: float = 1
        self.scale_y: float = 1

    ### GRAPH MANAGEMENT FUNCTIONS 

    def load_nav_graph(self, file_path: str) -> Tuple[bool, str]:
        """Load navigation graph from JSON file Core Logic """
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                level_name = next(iter(data["levels"]))
                self.nav_graph = data["levels"][level_name]
                self._initialize_vertex_data()
                self._calculate_scaling_factors()
            return True, "Graph loaded successfully"
        except Exception as e:
            return False, f"Error loading file: {str(e)}"

    def _initialize_vertex_data(self):
        """Initialize vertex colors and names with  naming """
        self.vertex_colors = {}
        self.vertex_names = {}
        prefixes = ["North", "South", "East", "West", "Central", "Main", "Gate", "Hub"]
        suffixes = ["Entrance", "Exit", "Junction", "Terminal", "Node", "Point", "Station", "Zone"]
        
        for idx, vertex in enumerate(self.nav_graph["vertices"]):
            self.vertex_colors[idx] = f"#{random.randint(0, 0xFFFFFF):06x}"
            
            if len(vertex) > 2 and isinstance(vertex[2], dict) and "name" in vertex[2]:
                self.vertex_names[idx] = vertex[2]["name"]
            else:
                if idx < len(prefixes):
                    if idx % 2 == 0:
                        self.vertex_names[idx] = f"{prefixes[idx]} {suffixes[idx]}"
                    else:
                        self.vertex_names[idx] = f"{prefixes[idx]}-{suffixes[idx]}"
                else:
                    letter = chr(65 + (idx % 26))  # A-Z
                    number = (idx // 26) + 1
                    self.vertex_names[idx] = f"{letter}{number}"
            
            if self.vertex_names[idx] in list(self.vertex_names.values())[:idx]:
                self.vertex_names[idx] = f"{self.vertex_names[idx]}_{idx}"

    def _calculate_scaling_factors(self, canvas_width: int = 800, canvas_height: int = 600):
        """Calculate scaling factors for proper graph display"""
        vertices = self.nav_graph["vertices"]
        if not vertices:
            return
            
        self.min_x = min(v[0] for v in vertices)
        self.max_x = max(v[0] for v in vertices)
        self.min_y = min(v[1] for v in vertices)
        self.max_y = max(v[1] for v in vertices)
        
        graph_width = self.max_x - self.min_x
        graph_height = self.max_y - self.min_y
        
        if graph_width > 0:
            self.scale_x = (canvas_width - 2 * self.padding) / graph_width
        if graph_height > 0:
            self.scale_y = (canvas_height - 2 * self.padding) / graph_height

    ### ROBOT MANAGEMENT FUNCTIONS 

    def spawn_robot(self, vertex_idx: int, canvas) -> Tuple[Optional[Robot], str]:
        """Spawn a new robot at the specified vertex (allows multiple robots per vertex)"""
        if not self.nav_graph or vertex_idx >= len(self.nav_graph["vertices"]):
            return None, "Invalid vertex index"
        
        self.robot_counter += 1
        robot_id = f"R{self.robot_counter}" 
        vertex = self.nav_graph["vertices"][vertex_idx]
        
        robot = Robot(
            robot_id=robot_id,
            position=vertex,
            canvas=canvas,
            vertex_colors=self.vertex_colors,
            fleet_manager=self,
            padding=self.padding,
            min_x=self.min_x,
            min_y=self.min_y,
            scale_x=self.scale_x,
            scale_y=self.scale_y
        )
        
        robot.spawn()  
        self.robots.append(robot)  
        return robot, f"Spawned at {self.vertex_names[vertex_idx]}"

    def set_robot_destination(self, robot_id: str, vertex_idx: int) -> Tuple[bool, str]:
        """Set destination for a specific robot with occupancy check"""
        if not self.nav_graph or vertex_idx >= len(self.nav_graph["vertices"]):
            return False, "Invalid vertex index"
        
        for robot in self.robots:
            if (self.get_vertex_index(robot.position) == vertex_idx and 
                robot.robot_id != robot_id):  
                return False, f"Vertex {self.vertex_names.get(vertex_idx, '')} occupied by {robot.robot_id}"
        
        robot = next((r for r in self.robots if r.robot_id == robot_id), None)
        if not robot:
            return False, f"Robot {robot_id} not found"
            
        current_idx = self.get_vertex_index(robot.position)
        if current_idx == vertex_idx:
            return False, "Cannot set destination to current position"
            
        target_vertex = self.nav_graph["vertices"][vertex_idx]
        self.robot_destinations[robot_id] = target_vertex
        return True, f"Destination set to {self.vertex_names.get(vertex_idx, '')}"
    
    def get_robot_by_id(self, robot_id):
        """Get robot by its ID"""
        return next((r for r in self.robots if r.robot_id == robot_id), None)
    
    def spawn_robot_threadsafe(self, vertex_idx: int, canvas) -> Tuple[Optional[Robot], str]:
        """Thread-safe robot spawning"""
        with threading.Lock():
            robot, message = self.spawn_robot(vertex_idx, canvas)
            if robot:
                self._assign_initial_task(robot)
            return robot, message
        
    def get_robot_status(self, robot_id: str) -> Optional[dict]:
        """Get status of specific robot"""
        robot = next((r for r in self.robots if r.robot_id == robot_id), None)
        if robot:
            return {
                "id": robot.robot_id,
                "position": robot.position,
                "status": robot.status,
                "vertex_name": self.get_vertex_name(robot.position)
            }
        return None
    
    def select_robot(self, position: tuple) -> Optional[Robot]:
        """Select robot at given position"""
        for robot in self.robots:
            if (robot.position[0] == position[0] and 
                robot.position[1] == position[1]):
                self.selected_robot = robot
                return robot
        self.selected_robot = None
        return None
    
    def on_canvas_click(self, event):
        """Handle general canvas clicks for robot selection"""
        if not self.fleet_manager.nav_graph or not self.fleet_manager.robots:
            return
            
        for robot in self.fleet_manager.robots:
            x, y = self.fleet_manager.get_canvas_coords(robot.position)
            if ((event.x - x)**2 + (event.y - y)**2) <= (self.fleet_manager.vertex_radius**2):
                self.select_robot(robot)
                return
            
        self.deselect_robot()

    def clear_all(self) -> str:
        """Clear all robots and reset state"""
        self.robots = []
        self.robot_counter = 0
        self.robot_destinations = {}
        self.selected_robot = None
        return "System reset complete"
    
    ### PATHFINDING AND MOVEMENT 

    def get_all_robots_status(self) -> List[dict]:
        """Get status of all robots"""
        return [self.get_robot_status(r.robot_id) for r in self.robots]
    
    def find_path(self, start_idx: int, end_idx: int) -> List[int]:
        """Find path through edges using BFS"""
        if start_idx == end_idx:
            return []
            
        queue = deque()
        queue.append((start_idx, [start_idx]))  
        visited = set()
        visited.add(start_idx)
        
        while queue:
            current_idx, path = queue.popleft()
            
            for lane in self.nav_graph["lanes"]:
                if lane[0] == current_idx:
                    neighbor = lane[1]
                elif lane[1] == current_idx:  
                    neighbor = lane[0]
                else:
                    continue
                    
                if neighbor == end_idx:
                    return path + [neighbor]
                    
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return [] 
    
    def calculate_path_along_edges(self, start_idx: int, end_idx: int) -> List[tuple]:
        """
        Generate smooth path points between two vertices
        """
        path_indices = PathFinder.find_path(
            self.nav_graph,
            start_idx,
            end_idx
        )
        
        if not path_indices:
            return []

        path_points = []
        vertices = self.nav_graph["vertices"]
        
        for i in range(len(path_indices)-1):
            start = vertices[path_indices[i]]
            end = vertices[path_indices[i+1]]
            
            steps = max(3, int(self.distance(start, end) / 10)) 
            
            for j in range(steps + 1):
                ratio = j / steps
                x = start[0] + (end[0] - start[0]) * ratio
                y = start[1] + (end[1] - start[1]) * ratio
                path_points.append((x, y))
        
        return path_points
    
    def find_and_interpolate_path(self, start_idx: int, end_idx: int) -> List[tuple]:
        """Find path and interpolate points (combines both operations)"""
        path_indices = PathFinder.find_path(
            self.nav_graph,
            start_idx,
            end_idx
        )
        return self.calculate_path_along_edges(path_indices) if path_indices else []
    
    def move_robot_concurrently(self, robot, target_pos, gui_update_callback):
        """Thread-safe movement with proper destination handling"""
        try:
            while True:
                if self.has_reached_destination(robot.position, target_pos):
                    robot.set_status("idle")
                    gui_update_callback(robot, "idle")
                    break
                    
                path_indices = self.find_path_to_destination(robot.position, target_pos)
                if not path_indices:
                    robot.set_status("blocked")
                    gui_update_callback(robot, "blocked")
                    time.sleep(1)
                    continue
                    
                if not self.traffic_manager.reserve_path(robot.robot_id, path_indices):
                    robot.set_status("waiting")
                    gui_update_callback(robot, "waiting")
                    time.sleep(0.5)
                    continue
                    
                path_points = self.calculate_path_along_edges(path_indices)
                for point in path_points:
                    if self.has_reached_destination(robot.position, target_pos):
                        break
                        
                    robot.position = point
                    robot.set_status("moving")
                    gui_update_callback(robot, "moving")
                    time.sleep(0.1)
                    
                self.traffic_manager.release_path(robot.robot_id, path_indices)
                
        except Exception as e:
            robot.set_status("error")
            gui_update_callback(robot, "error")
            print(f"Movement error for {robot.robot_id}: {str(e)}")

    def calculate_path(self, start_pos: tuple, end_pos: tuple) -> List[tuple]:
        """Calculate path from start to end position"""
        path = []
        for i in range(self.navigation_steps + 1):
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * (i/self.navigation_steps)
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * (i/self.navigation_steps)
            path.append((x, y))
        return path

    def start_movement(self, gui_callback) -> Tuple[bool, List[str]]:
        """Move robots along graph edges"""
        if not self.robot_destinations:
            return False, ["No destinations set"]
        
        movement_logs = []
        for robot in self.robots:
            if robot.robot_id in self.robot_destinations:
                start_idx = self.get_vertex_index(robot.position)
                end_idx = self.get_vertex_index(self.robot_destinations[robot.robot_id])
                
                if start_idx == -1 or end_idx == -1:
                    movement_logs.append(f"{robot.robot_id}: Invalid start/end position")
                    continue
                    
                path_points = self.calculate_path_along_edges(start_idx, end_idx)
                
                if not path_points:
                    movement_logs.append(f"{robot.robot_id} cannot reach destination")
                    continue
                    
                for point in path_points:
                    robot.position = point
                    gui_callback(robot)
                    time.sleep(self.navigation_delay/len(path_points))
                
                movement_logs.append(
                    f"{robot.robot_id} reached {self.get_vertex_name_by_index(end_idx)}"
                )
        
        self.robot_destinations.clear()
        return True, movement_logs
    
    def interpolate_path_points(self, vertex_path: List[int]) -> List[tuple]:
        """Convert vertex indices to smooth path points"""
        if not vertex_path or not self.nav_graph:
            return []
            
        path_points = []
        vertices = self.nav_graph["vertices"]
        
        for i in range(len(vertex_path)-1):
            start = vertices[vertex_path[i]]
            end = vertices[vertex_path[i+1]]
            steps = max(3, int(self.distance(start, end) / 10))
            
            for j in range(steps + 1):
                ratio = j / steps
                x = start[0] + (end[0] - start[0]) * ratio
                y = start[1] + (end[1] - start[1]) * ratio
                path_points.append((x, y))
                
        return path_points

    def find_and_interpolate_path(self, start_idx: int, end_idx: int) -> List[tuple]:
        """Combined pathfinding and interpolation"""
        path_indices = PathFinder.find_path(
            self.nav_graph,
            start_idx,
            end_idx
        )
        return self.interpolate_path_points(path_indices) if path_indices else []


    def distance(self, p1: tuple, p2: tuple) -> float:
        """Calculate Euclidean distance between two points"""
        return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
    
    def _get_verified_new_destination(self, current_pos):
        """Safe destination selection"""
        current_idx = self.get_vertex_index(current_pos)
        if current_idx == -1:
            return current_pos
        
        available = [i for i in range(len(self.nav_graph["vertices"])) 
                    if i != current_idx]
        return self.nav_graph["vertices"][random.choice(available)] if available else current_pos

    ### TRAFFIC MANAGEMENT INTEGRATION 

    def get_lane_status(self, lane: tuple) -> str:
        """Get traffic light status for visualization."""
        return self.traffic_manager.get_lane_status(lane)
    
    def _path_to_lanes(self, path_indices: List[int]) -> List[tuple]:
        """Convert path indices to lane tuples."""
        if not path_indices or len(path_indices) < 2:
            return []
        return [(path_indices[i], path_indices[i+1]) 
                for i in range(len(path_indices)-1)]
    
    def find_path_to_destination(self, current_pos, target_pos):
        """Find path with congestion awareness"""
        start_idx = self.get_vertex_index(current_pos)
        end_idx = self.get_vertex_index(target_pos)
        if start_idx == -1 or end_idx == -1:
            return None
        return self.traffic_manager.find_least_congested_path(
            self.nav_graph, start_idx, end_idx)
    
    ### VISUALIZATION 

    def get_canvas_coords(self, vertex: tuple) -> tuple:
        """Convert graph coordinates to canvas coordinates"""
        return (
            self.padding + (vertex[0] - self.min_x) * self.scale_x,
            self.padding + (vertex[1] - self.min_y) * self.scale_y
        )
    
    def update_visualization(self):
        """Update lane colors for visualization."""
        for lane in self.nav_graph.get("lanes", []):
            status = self.get_lane_status(lane)
            self.lane_status[lane] = status

    def clear_path_reservations(self, robot_id):
        """Clear all path reservations for a robot"""
        if hasattr(self, 'traffic_manager'):
            self.traffic_manager.release_all_for_robot(robot_id)
            
    ### UTILITY FUNCTION 

    def distance(self, p1: tuple, p2: tuple) -> float:
        """Calculate distance between two points"""
        return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
    
    def get_vertex_name_by_index(self, idx: int) -> str:
        """Get vertex name by index"""
        return self.vertex_names.get(idx, f"Vertex-{idx}")
    
    def _has_reached_destination(self, current_pos, target_pos):
        """Exact position matching"""
        current = (round(current_pos[0]), round(current_pos[1]) if len(current_pos) > 1 else (round(current_pos[0]), 0))
        target = (round(target_pos[0]), round(target_pos[1]) if len(target_pos) > 1 else (round(target_pos[0]), 0))
        return current == target
    
    ### CONCURRENT MOVEMENT 

    def start_concurrent_movement(self, gui_update_callback):
        """Start all robot movements in separate threads"""
        threads = []
        for robot in self.robots:
            if robot.robot_id in self.robot_destinations:
                target = self.robot_destinations[robot.robot_id]
                t = threading.Thread(
                    target=self.move_robot_concurrently,
                    args=(robot, target, gui_update_callback),
                    daemon=True
                )
                threads.append(t)
                t.start()
        
        self.threads = threads

    def calculate_path_along_edges(self, vertex_path: List[int]) -> List[tuple]:
        """Generate interpolated points from existing vertex path"""
        if not vertex_path:
            return []
            
        path_points = []
        vertices = self.nav_graph["vertices"]
        
        for i in range(len(vertex_path)-1):
            start = vertices[vertex_path[i]]
            end = vertices[vertex_path[i+1]]
            
            steps = max(3, int(self.distance(start, end) / 10))
            for j in range(steps + 1):
                ratio = j / steps
                x = start[0] + (end[0] - start[0]) * ratio
                y = start[1] + (end[1] - start[1]) * ratio
                path_points.append((x, y))
        
        
        return path_points


    def _assign_initial_task(self, robot: Robot) -> None:
        """Assign first task to newly spawned robot"""
        current_idx = self.get_vertex_index(robot.position)
        available = [i for i in range(len(self.nav_graph["vertices"])) 
                if i != current_idx]
        if available:
            dest_idx = random.choice(available)
            self.set_robot_destination(robot.robot_id, dest_idx)
            self.start_robot_thread(robot)

    def start_robot_thread(self, robot: Robot) -> None:
        """Start movement thread for a robot"""
        threading.Thread(
            target=self.move_robot_concurrently,
            args=(robot, self.robot_destinations[robot.robot_id], self.safe_gui_update),
            daemon=True
        ).start()

    ### GET VERTEX 

    def get_vertex_index(self, position: tuple) -> int:
        """Find index of vertex by position coordinates with dimension safety"""
        if not self.nav_graph:
            return -1
            
        pos_x = position[0]
        pos_y = position[1] if len(position) > 1 else 0
        
        for idx, vertex in enumerate(self.nav_graph["vertices"]):
            vertex_x = vertex[0]
            vertex_y = vertex[1] if len(vertex) > 1 else 0
            if (abs(vertex_x - pos_x) < 0.001 and 
                abs(vertex_y - pos_y) < 0.001):
                return idx
        return -1

    def get_vertex_name(self, vertex: tuple) -> str:
        """Get name from vertex coordinates"""
        idx = self.get_vertex_index(vertex)
        return self.vertex_names.get(idx, "Unknown")

    def get_all_vertex_names(self) -> Dict[int, str]:
        """Get all vertex names"""
        return self.vertex_names
    
    def get_vertex_name_by_position(self, position: tuple) -> str:
        """Get vertex name by position coordinates"""
        idx = self.get_vertex_index(position)
        return self.get_vertex_name_by_index(idx)

    def on_vertex_click(self, vertex_idx):
        """Handle vertex clicks to spawn robots"""
        if not self.fleet_manager.nav_graph:
            return
            
        robot, message = self.fleet_manager.spawn_robot(vertex_idx, self.canvas)
        if robot:
            self.add_history_entry(robot.robot_id, message)
            self.prompt_destination(robot)
            self.start_button.config(state=tk.NORMAL)

    def has_reached_destination(self, current_pos, target_pos):
        """Public method for destination checking"""
        return self._has_reached_destination(current_pos, target_pos)
    
    def _has_reached_destination(self, current_pos, target_pos, threshold=0.05):
        """Exact position matching with rounding"""
        current = (round(current_pos[0], round(current_pos[1])) if len(current_pos) > 1 
                 else (round(current_pos[0]), 0))
        target = (round(target_pos[0]), round(target_pos[1]) if len(target_pos) > 1 
                else (round(target_pos[0]), 0))
        return current == target
    