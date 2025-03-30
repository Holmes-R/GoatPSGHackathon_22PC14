from tkinter import Tk
import math
import tkinter as tk
import time

class Robot:
    def __init__(self, robot_id, position, fleet_manager, canvas, vertex_colors, padding, min_x, min_y, scale_x, scale_y):
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
        
        self.status_colors = {
            "moving": "#00FF00",
            "waiting": "#FFFF00",
            "charging": "#0000FF",
            "idle": "#AAAAAA",
            "blocked": "#FF0000",
            "error": "#FFA500"
        }

        self.current_task = None
        self.task_complete_callback = None

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

        def assign_task(self, destination, callback=None):
            """Assign a new task to the robot"""
            self.current_task = destination
            self.task_complete_callback = callback
            self.set_status("task_assigned")

    def update_visualization(self):
        """Update robot's visual position and status"""
        x, y = self._get_canvas_coords()
        
        # Calculate offset for multiple robots at same position
        same_pos_robots = [r for r in self.fleet_manager.robots 
                         if r.position == self.position]
        index = same_pos_robots.index(self)
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
        # Clear previous effects
        if hasattr(self, 'effect_id') and self.effect_id:
            self.canvas.delete(self.effect_id)
        
        # Add new effects
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

    def _flash_warning(self):
        """Animate waiting status with flashing effect"""
        if self.status == "waiting" and hasattr(self, 'effect_id'):
            current_color = self.canvas.itemcget(self.effect_id, "outline")
            new_color = "#FFCC00" if current_color == "#FFFF00" else "#FFFF00"
            self.canvas.itemconfig(self.effect_id, outline=new_color)
            self.canvas.after(500, self._flash_warning)

    def move(self, new_position):
        """Modified move method"""
        with self.position_lock:
            if self.status == "idle":
                return False  # Movement blocked when idle
            self.position = new_position
            return True

    def set_status(self, status):
        """Update robot status and visuals"""
        self.status = status
        self.update_visualization()

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

    def _get_canvas_coords(self):
        """Convert graph coordinates to canvas coordinates"""
        px = self.position[0]
        py = self.position[1] if len(self.position) > 1 else 0
        return (
            self.padding + (px - self.min_x) * self.scale_x,
            self.padding + (py - self.min_y) * self.scale_y
        )

    def _get_vertex_color(self):
        """Get color from current vertex"""
        idx = self._find_vertex_index()
        return self.vertex_colors.get(idx, "#00FF00")