import time

class Robot:
    def __init__(self, robot_id, position, canvas, vertex_colors, padding, min_x, min_y, scale_x, scale_y):
        self.robot_id = robot_id
        self.position = position
        self.canvas = canvas
        self.vertex_colors = vertex_colors
        self.padding = padding
        self.min_x = min_x
        self.min_y = min_y
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.status = "waiting"
        self.last_action = "Initialized"
        self.robot_obj = None
        self.label_obj = None

    def spawn(self):
        """Create visual representation of the robot"""
        x, y = self._get_canvas_coords()
        color = self.vertex_colors.get(self.get_vertex_index(), "green")
        
        self.robot_obj = self.canvas.create_oval(
            x-10, y-10, x+10, y+10,
            fill=color, outline="black", width=2
        )
        
        self.label_obj = self.canvas.create_text(
            x, y-15,
            text=f"{self.robot_id}", 
            font=("Arial", 8, "bold"), 
            fill="black"
        )
        self.last_action = "Spawned"
        self.status = "waiting"

    def move(self, new_position):
        """Move robot to new position"""
        self.position = new_position
        x, y = self._get_canvas_coords()
        
        self.canvas.coords(self.robot_obj, x-10, y-10, x+10, y+10)
        self.canvas.coords(self.label_obj, x, y-15)
        
        # Update color to match new vertex
        new_color = self.vertex_colors.get(self.get_vertex_index(), "green")
        self.canvas.itemconfig(self.robot_obj, fill=new_color)
        
        self.last_action = f"Moved to new position ({new_position[0]:.1f}, {new_position[1]:.1f})"
        self.status = "waiting"

    def set_status(self, status):
        """Update robot status"""
        self.status = status
        color_map = {
            "waiting": "green",
            "moving": "red",
            "charging": "yellow",
            "task complete": "blue"
        }
        self.canvas.itemconfig(self.robot_obj, fill=color_map.get(status, "green"))
        self.last_action = f"Status changed to {status}"

    def get_status(self):
        """Get current status"""
        return self.status

    def _get_canvas_coords(self):
        """Convert graph coordinates to canvas coordinates"""
        return (
            self.padding + (self.position[0] - self.min_x) * self.scale_x,
            self.padding + (self.position[1] - self.min_y) * self.scale_y
        )

    def get_vertex_index(self):
        """Get index of current vertex (implementation depends on your graph structure)"""
        # This should be implemented based on how you track vertices
        return -1