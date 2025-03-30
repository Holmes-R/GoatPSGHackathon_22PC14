from tkinter import Tk
import math
import tkinter as tk
import time
import threading
from src.utils.logger import robot_logger

class Robot:
    def __init__(self, robot_id, position, fleet_manager, canvas, vertex_colors, padding, min_x, min_y, scale_x, scale_y, spawn_vertex=None, initial_destination=None):
        self.robot_id = robot_id
        self.position = (position[0], position[1]) if len(position) > 1 else (position[0], 0)
        self.canvas = canvas
        self.fleet_manager = fleet_manager  
        self.vertex_colors = vertex_colors
        self.padding = padding
        self.min_x = min_x
        self.min_y = min_y
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.status = "waiting"
        self.robot_obj = None
        self.label_obj = None
        self.effect_id = None
        self.waiting_effect = None
        self.path = []
        self.path_history = []
        self.current_step = 0
        self.battery_level = 100  
        self.position_lock = threading.Lock()
        
        vertex_name = fleet_manager.get_vertex_name(position)
        robot_logger.log_event(
            robot_id=robot_id,
            action="SPAWN",
            path=vertex_name,
            status="SUCCESS",
            battery=self.battery_level
        )
        
        self.current_vertex = spawn_vertex if spawn_vertex else self._find_vertex_name()
        self.destination = initial_destination
        
        robot_logger.log_event(
            robot_id=self.robot_id,
            action="INITIALIZE",
            source_vertex=self.current_vertex,
            destination_vertex=initial_destination,
            battery=self.battery_level
        )
        
        self.status_colors = {
            "moving": "#00FF00",
            "waiting": "#FFFF00",
            "charging": "#0000FF",
            "idle": "#AAAAAA",
            "blocked": "#FF0000",
            "error": "#FFA500",
            "task_assigned": "#FF00FF"
        }

        self.current_task = None
        self.task_complete_callback = None
        self.spawn()
        if initial_destination:
            self.move_to_destination(initial_destination)

    def spawn(self):
        """Create visual representation of the robot"""
        x, y = self._get_canvas_coords()
        color = self.vertex_colors.get(self._find_vertex_index(), "#00FF00")
        
        self.robot_obj = self.canvas.create_oval(
            x-10, y-10, x+10, y+10,
            fill=color, outline="black", width=2
        )
        
        self.label_obj = self.canvas.create_text(
            x, y-15,
            text=self.robot_id,
            font=("Arial", 8, "bold")
        )
        self.update_visualization()

    def assign_task(self, destination, callback=None):
        """Updated task assignment using new movement system"""
        self.current_task = destination
        self.task_complete_callback = callback
        
        robot_logger.log_action(
            robot_id=self.robot_id,
            action="TASK_ASSIGNED",
            destination=self._get_vertex_name(destination),
            status="PENDING"
        )
        
        if self.move_to_destination(destination):
            self.complete_task()

    def update_visualization(self):
        """Update robot's visual position and status"""
        x, y = self._get_canvas_coords()
        
        same_pos_robots = [r for r in self.fleet_manager.robots 
                         if r.position == self.position]
        index = same_pos_robots.index(self) if self in same_pos_robots else 0
        angle = index * (2 * math.pi / max(6, len(same_pos_robots)))
        offset_x = 15 * math.cos(angle)
        offset_y = 15 * math.sin(angle)
        
        if not hasattr(self, 'robot_obj'):
            self.spawn()
        else:
            self.canvas.coords(
                self.robot_obj,
                x-10+offset_x, y-10+offset_y,
                x+10+offset_x, y+10+offset_y
            )
            self.canvas.coords(
                self.label_obj,
                x+offset_x, y-15+offset_y
            )
            self.canvas.itemconfig(
                self.robot_obj,
                fill=self.status_colors.get(self.status, "#AAAAAA")
            )
        
        self._update_status_effects(x+offset_x, y+offset_y)

    def _update_status_effects(self, x, y):
        """Update visual effects based on status"""
        if hasattr(self, 'effect_id') and self.effect_id:
            self.canvas.delete(self.effect_id)
        
        if self.status == "moving":
            self.effect_id = self.canvas.create_line(
                x, y, x+20, y,
                arrow=tk.LAST, fill="#00FF00", width=2,
                tags="moving_effect"
            )
        elif self.status == "waiting":
            self.effect_id = self.canvas.create_oval(
                x-15, y-15, x+15, y+15,
                outline="#FFFF00", width=2, dash=(5,2),
                tags="waiting_effect"
            )
            self._flash_warning()
        elif self.status == "blocked":
            self.effect_id = self.canvas.create_oval(
                x-15, y-15, x+15, y+15,
                outline="#FF0000", width=3,
                tags="blocked_effect"
            )
        elif self.status == "charging":
            self.effect_id = self.canvas.create_text(
                x, y+20,
                text="⚡", font=("Arial", 12),
                tags="charging_effect"
            )
        elif self.status == "task_assigned":
            self.effect_id = self.canvas.create_text(
                x, y+20,
                text="★", font=("Arial", 12),
                fill="#FF00FF",
                tags="task_effect"
            )

    def _flash_warning(self):
        """Animate waiting status with flashing effect"""
        if self.status == "waiting" and hasattr(self, 'effect_id'):
            current_color = self.canvas.itemcget(self.effect_id, "outline")
            new_color = "#FFCC00" if current_color == "#FFFF00" else "#FFFF00"
            self.canvas.itemconfig(self.effect_id, outline=new_color)
            self.canvas.after(500, self._flash_warning)

    def move(self, new_position):
        """Move robot to new position with logging"""
        with self.position_lock:
            if self.status == "idle":
                return False
            
            old_vertex = self._find_vertex_name()
            self.position = new_position
            new_vertex = self._find_vertex_name()
            
            robot_logger.log_action(
                robot_id=self.robot_id,
                action="MOVE",
                path=f"{old_vertex}->{new_vertex}",
                status="SUCCESS",
                battery=self.battery
            )
            
            self.current_vertex = new_vertex
            self.update_visualization()
            return True

    def set_status(self, status, reason=None):
        """Update robot status with optional logging"""
        self.status = status
        self.update_visualization()
        
        if status in ["waiting", "blocked", "charging"]:
            robot_logger.log_action(
                robot_id=self.robot_id,
                action=f"STATUS_{status.upper()}",
                reason=reason,
                battery=self.battery
            )

    def wait(self, duration, reason="Traffic"):
        """Handle waiting with logging"""
        self.set_status("waiting", reason)
        
        robot_logger.log_action(
            robot_id=self.robot_id,
            action="WAIT",
            status="PENDING",
            duration=duration,
            reason=reason,
            battery=self.battery
        )
        
        def finish_wait():
            self.set_status("idle")
            robot_logger.log_action(
                robot_id=self.robot_id,
                action="WAIT",
                status="COMPLETED",
                duration=duration,
                reason=reason,
                battery=self.battery
            )
        
        self.canvas.after(int(duration * 1000), finish_wait)

    def update_destination(self, new_destination):
        """Update target destination with logging"""
        self.destination = new_destination
        robot_logger.log_action(
            robot_id=self.robot_id,
            action="DESTINATION_UPDATE",
            path=f"{self.current_vertex}->{new_destination}",
            battery=self.battery
        )

    def _find_vertex_index(self):
        """Find vertex index by current position"""
        if not hasattr(self.fleet_manager, 'nav_graph'):
            return 0
            
        for idx, vertex in enumerate(self.fleet_manager.nav_graph["vertices"]):
            vx = vertex[0]
            vy = vertex[1] if len(vertex) > 1 else 0
            px, py = self.position[0], self.position[1] if len(self.position) > 1 else 0
            if abs(vx - px) < 0.001 and abs(vy - py) < 0.001:
                return idx
        return 0

    def _find_vertex_name(self):
        """Get the name of the current vertex"""
        idx = self._find_vertex_index()
        if hasattr(self.fleet_manager, 'nav_graph') and 'vertex_names' in self.fleet_manager.nav_graph:
            return self.fleet_manager.nav_graph['vertex_names'][idx]
        return f"Vertex_{idx}"

    def _get_canvas_coords(self):
        """Convert graph coordinates to canvas coordinates"""
        px = self.position[0]
        py = self.position[1] if len(self.position) > 1 else 0
        return (
            self.padding + (px - self.min_x) * self.scale_x,
            self.padding + (py - self.min_y) * self.scale_y
        )

    def complete_task(self):
        """Handle task completion with logging"""
        if self.current_task:
            robot_logger.log_action(
                robot_id=self.robot_id,
                action="TASK_COMPLETE",
                task=self.current_task,
                status="SUCCESS",
                battery=self.battery
            )
            
            if self.task_complete_callback:
                self.task_complete_callback(self.robot_id, self.current_task)
            
            self.current_task = None
            self.set_status("idle")

    def move_to_destination(self, destination_position):
        """Enhanced movement method with complete logging"""
        start_vertex = self._find_vertex_name()
        
        robot_logger.log_action(
            robot_id=self.robot_id,
            action="MOVE_START",
            path=f"{start_vertex}->{self._get_vertex_name(destination_position)}",
            status="IN_PROGRESS",
            battery=self.battery
        )
        
        success = self._execute_movement(destination_position)
        end_vertex = self._find_vertex_name()
        
        if success:
            robot_logger.log_action(
                robot_id=self.robot_id,
                action="MOVE_COMPLETE",
                path=f"{start_vertex}->{end_vertex}",
                status="SUCCESS",
                battery=self.battery,
                distance=self._calculate_move_distance(start_vertex, end_vertex)
            )
            self.current_vertex = end_vertex
        else:
            robot_logger.log_action(
                robot_id=self.robot_id,
                action="MOVE_FAILED",
                path=f"{start_vertex}->{end_vertex}",
                status="FAILED",
                battery=self.battery,
                reason="Obstacle"
            )
        return success

    def _execute_movement(self, target_position):
        """Actual movement implementation with debug"""
        print(f"Attempting movement to {target_position}")  
        try:
            path = self.fleet_manager.calculate_path(self.position, target_position)
            print(f"Calculated path: {path}") 
            
            for step in path:
                with self.position_lock:
                    self.position = step
                    self.update_visualization()
                    print(f"Moved to {step}")  
                    time.sleep(0.1)
                    
            print("Movement completed successfully")  
            return True
            
        except Exception as e:
            print(f"Movement failed: {str(e)}")  
            return False

    def _calculate_move_distance(self, start_vertex, end_vertex):
        """Calculate actual distance moved"""
        if not hasattr(self.fleet_manager, 'nav_graph'):
            return 0.0
        
        try:
            start_idx = self.fleet_manager.nav_graph['vertex_names'].index(start_vertex)
            end_idx = self.fleet_manager.nav_graph['vertex_names'].index(end_vertex)
            start_pos = self.fleet_manager.nav_graph['vertices'][start_idx]
            end_pos = self.fleet_manager.nav_graph['vertices'][end_idx]
            return math.dist(start_pos, end_pos)
        except (ValueError, IndexError):
            return 0.0