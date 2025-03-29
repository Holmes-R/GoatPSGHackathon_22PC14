import json
import random
from typing import Dict, List, Optional, Tuple
from src.models.robots import Robot
import time
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
        
        # Visualization parameters
        self.padding: int = 50
        self.vertex_radius: int = 15
        self.min_x: float = 0
        self.max_x: float = 0
        self.min_y: float = 0
        self.max_y: float = 0
        self.scale_x: float = 1
        self.scale_y: float = 1

    def load_nav_graph(self, file_path: str) -> Tuple[bool, str]:
        """Load navigation graph from JSON file"""
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
        """Initialize vertex colors and names with improved naming logic"""
        self.vertex_colors = {}
        self.vertex_names = {}
        
        # Available naming components
        prefixes = ["North", "South", "East", "West", "Central", "Main", "Gate", "Hub"]
        suffixes = ["Entrance", "Exit", "Junction", "Terminal", "Node", "Point", "Station", "Zone"]
        
        for idx, vertex in enumerate(self.nav_graph["vertices"]):
            # Generate random color for vertex
            self.vertex_colors[idx] = f"#{random.randint(0, 0xFFFFFF):06x}"
            
            # Determine vertex name
            if len(vertex) > 2 and isinstance(vertex[2], dict) and "name" in vertex[2]:
                # Use name from graph data if available
                self.vertex_names[idx] = vertex[2]["name"]
            else:
                # Generate descriptive name if not provided
                if idx < len(prefixes):
                    # Use predefined names for first few vertices
                    if idx % 2 == 0:
                        self.vertex_names[idx] = f"{prefixes[idx]} {suffixes[idx]}"
                    else:
                        self.vertex_names[idx] = f"{prefixes[idx]}-{suffixes[idx]}"
                else:
                    # For additional vertices, use letter-number combination
                    letter = chr(65 + (idx % 26))  # A-Z
                    number = (idx // 26) + 1
                    self.vertex_names[idx] = f"{letter}{number}"
            
            # Ensure name is unique
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

    def get_canvas_coords(self, vertex: tuple) -> tuple:
        """Convert graph coordinates to canvas coordinates"""
        return (
            self.padding + (vertex[0] - self.min_x) * self.scale_x,
            self.padding + (vertex[1] - self.min_y) * self.scale_y
        )


    def spawn_robot(self, vertex_idx: int, canvas) -> Tuple[Optional[Robot], str]:
        """Spawn a new robot at specified vertex"""
        if not self.nav_graph or vertex_idx >= len(self.nav_graph["vertices"]):
            return None, "Invalid vertex index"

        self.robot_counter += 1
        robot_id = f"R{self.robot_counter}"
        vertex = self.nav_graph["vertices"][vertex_idx]
        vertex_name = self.vertex_names[vertex_idx]
        
        robot = Robot(
            robot_id=robot_id,
            position=vertex,
            canvas=canvas,
            vertex_colors=self.vertex_colors,  # Pass vertex_colors
            padding=self.padding,
            min_x=self.min_x,
            min_y=self.min_y,
            scale_x=self.scale_x,
            scale_y=self.scale_y
        )
        
        robot.spawn()
        self.robots.append(robot)
        return robot, f"Spawned at {vertex_name}"

    def set_robot_destination(self, robot_id: str, vertex_idx: int) -> Tuple[bool, str]:
        """Set destination for a specific robot"""
        if not self.nav_graph or vertex_idx >= len(self.nav_graph["vertices"]):
            return False, "Invalid vertex index"
        
        robot = next((r for r in self.robots if r.robot_id == robot_id), None)
        if not robot:
            return False, f"Robot {robot_id} not found"
            
        current_idx = self.get_vertex_index(robot.position)
        if current_idx == vertex_idx:
            return False, "Cannot set destination to current position"
            
        target_vertex = self.nav_graph["vertices"][vertex_idx]
        self.robot_destinations[robot_id] = target_vertex
        return True, f"Destination set to {self.vertex_names[vertex_idx]}"
    
    def calculate_path(self, start_pos: tuple, end_pos: tuple) -> List[tuple]:
        """Calculate path from start to end position"""
        # Simple linear interpolation for demonstration
        path = []
        for i in range(self.navigation_steps + 1):
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * (i/self.navigation_steps)
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * (i/self.navigation_steps)
            path.append((x, y))
        return path

    def start_movement(self, gui_callback) -> Tuple[bool, List[str]]:
        """Move all robots to their destinations with visualization"""
        if not self.robot_destinations:
            return False, ["No destinations set"]
        
        movement_logs = []
        for robot in self.robots:
            if robot.robot_id in self.robot_destinations:
                target = self.robot_destinations[robot.robot_id]
                path = self.calculate_path(robot.position, target)
                
                # Animate movement
                for step, new_pos in enumerate(path):
                    robot.position = new_pos
                    gui_callback(robot)  # Update GUI
                    time.sleep(self.navigation_delay/self.navigation_steps)
                    
                    if step == len(path)-1:
                        movement_logs.append(
                            f"{robot.robot_id} reached {self.get_vertex_name(target)}"
                        )
        
        self.robot_destinations.clear()
        return True, movement_logs

    def move_all_robots_randomly(self) -> Tuple[bool, List[str]]:
        """Move all robots to random vertices"""
        if not self.nav_graph:
            return False, ["No graph loaded"]
            
        movement_logs = []
        for robot in self.robots:
            current_idx = self.get_vertex_index(robot.position)
            available_indices = [i for i in range(len(self.nav_graph["vertices"])) 
                              if i != current_idx]
            if available_indices:
                next_idx = random.choice(available_indices)
                next_vertex = self.nav_graph["vertices"][next_idx]
                vertex_name = self.vertex_names[next_idx]
                
                robot.move(next_vertex)
                robot.set_status("moving")
                movement_logs.append(f"{robot.robot_id} randomly moved to {vertex_name}")
        
        return True, movement_logs

    def get_vertex_index(self, position: tuple) -> int:
        """Find index of vertex by position coordinates"""
        for idx, vertex in enumerate(self.nav_graph["vertices"]):
            if vertex[0] == position[0] and vertex[1] == position[1]:
                return idx
        return -1

    def get_vertex_name(self, vertex: tuple) -> str:
        """Get name from vertex coordinates"""
        idx = self.get_vertex_index(vertex)
        return self.vertex_names.get(idx, "Unknown")

    def get_all_vertex_names(self) -> Dict[int, str]:
        """Get all vertex names"""
        return self.vertex_names

    def select_robot(self, position: tuple) -> Optional[Robot]:
        """Select robot at given position"""
        for robot in self.robots:
            if (robot.position[0] == position[0] and 
                robot.position[1] == position[1]):
                self.selected_robot = robot
                return robot
        self.selected_robot = None
        return None

    def clear_all(self) -> str:
        """Clear all robots and reset state"""
        self.robots = []
        self.robot_counter = 0
        self.robot_destinations = {}
        self.selected_robot = None
        return "System reset complete"

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

    def get_all_robots_status(self) -> List[dict]:
        """Get status of all robots"""
        return [self.get_robot_status(r.robot_id) for r in self.robots]