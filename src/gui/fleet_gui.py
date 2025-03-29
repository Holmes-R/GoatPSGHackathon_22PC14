import tkinter as tk
from tkinter import filedialog, ttk, simpledialog, messagebox
import json
import random
from datetime import datetime
from src.models.robots import Robot

class FleetManagementApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Fleet Management System")
        
        # Configure main window layout with wider right panel
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas for graph visualization (60% width)
        self.canvas = tk.Canvas(self.main_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right panel for controls and history (40% width - much wider)
        self.right_panel = tk.Frame(self.main_frame, width=450, bg="#f0f0f0")  # Increased width to 450px
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        # Control buttons frame with improved layout
        self.button_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        self.button_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Larger buttons with consistent styling
        btn_style = {'width': 20, 'height': 1, 'font': ('Arial', 10)}
        self.load_button = tk.Button(self.button_frame, text="Load Graph", 
                                   command=self.load_nav_graph_file, **btn_style)
        self.load_button.pack(fill=tk.X, pady=3)
        
        self.move_button = tk.Button(self.button_frame, text="Move All Robots", 
                                   command=self.move_robots, state=tk.DISABLED, **btn_style)
        self.move_button.pack(fill=tk.X, pady=3)
        
        self.clear_button = tk.Button(self.button_frame, text="Clear Logs", 
                                    command=self.clear_logs, **btn_style)
        self.clear_button.pack(fill=tk.X, pady=3)
        
        # Separator
        ttk.Separator(self.right_panel, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Robot history display with much more space
        self.history_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # History label with larger font
        self.history_label = tk.Label(self.history_frame, 
                                     text="ROBOT HISTORY", 
                                     font=("Arial", 12, "bold"),
                                     bg="#f0f0f0")
        self.history_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Configure history tree with more width and rows
        self.history_tree = ttk.Treeview(self.history_frame, 
                                       columns=("Time", "Robot", "Event"), 
                                       show="headings", 
                                       height=20,  # More rows visible
                                       style="Custom.Treeview")
        
        # Style configuration for treeview
        style = ttk.Style()
        style.configure("Custom.Treeview", font=('Arial', 9), rowheight=25)
        style.configure("Custom.Treeview.Heading", font=('Arial', 10, 'bold'))
        
        # Set column widths (total width ~420px)
        self.history_tree.column("Time", width=100, anchor=tk.CENTER)
        self.history_tree.column("Robot", width=100, anchor=tk.CENTER)
        self.history_tree.column("Event", width=220, anchor=tk.W)  # Much wider event column
        
        self.history_tree.heading("Time", text="TIME")
        self.history_tree.heading("Robot", text="ROBOT")
        self.history_tree.heading("Event", text="EVENT")
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for history tree
        history_scroll = ttk.Scrollbar(self.history_tree, orient="vertical", command=self.history_tree.yview)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        # Frame for robot controls at the bottom
        self.robot_controls_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        self.robot_controls_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Robot management
        self.robots = []
        self.robot_counter = 0
        self.vertex_colors = {}
        self.vertex_names = {}
        self.nav_graph = None
        self.padding = 50
    
    def setup_ui_components(self):
        """Initialize all UI components separately for easy reset"""
        # Control buttons frame
        self.button_frame = tk.Frame(self.right_panel)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        self.load_button = tk.Button(self.button_frame, text="Load Graph", command=self.load_nav_graph_file, width=20)
        self.load_button.pack(fill=tk.X, pady=3)
        
        self.move_button = tk.Button(self.button_frame, text="Move All Robots", command=self.move_robots, state=tk.DISABLED, width=20)
        self.move_button.pack(fill=tk.X, pady=3)
        
        self.clear_button = tk.Button(self.button_frame, text="Clear Logs", command=self.clear_logs, width=20)
        self.clear_button.pack(fill=tk.X, pady=3)
        
        # Separator
        ttk.Separator(self.right_panel, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # History frame
        self.history_frame = tk.Frame(self.right_panel)
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        self.history_label = tk.Label(self.history_frame, text="ROBOT HISTORY", font=("Arial", 12, "bold"))
        self.history_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Create history treeview
        self.create_history_treeview()
        
        # Robot controls frame
        self.robot_controls_frame = tk.Frame(self.right_panel)
        self.robot_controls_frame.pack(fill=tk.X, pady=10, padx=5)

    def create_history_treeview(self):
        """Create or recreate the history treeview"""
        if hasattr(self, 'history_tree'):
            # Destroy old treeview if it exists
            self.history_tree.destroy()
        
        self.history_tree = ttk.Treeview(self.history_frame, 
                                       columns=("Time", "Robot", "Event"), 
                                       show="headings", 
                                       height=20)
        
        # Configure columns
        self.history_tree.column("Time", width=100, anchor=tk.CENTER)
        self.history_tree.column("Robot", width=100, anchor=tk.CENTER)
        self.history_tree.column("Event", width=220, anchor=tk.W)
        
        self.history_tree.heading("Time", text="TIME")
        self.history_tree.heading("Robot", text="ROBOT")
        self.history_tree.heading("Event", text="EVENT")
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        history_scroll = ttk.Scrollbar(self.history_tree, orient="vertical", command=self.history_tree.yview)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=history_scroll.set)



    def clear_logs(self):
        """Clear all logs and reset the system"""
        if not messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all logs and reset the system?"):
            return
        
        # Clear robots from canvas
        for robot in self.robots:
            if hasattr(robot, 'robot_obj'):
                self.canvas.delete(robot.robot_obj)
            if hasattr(robot, 'label_obj'):
                self.canvas.delete(robot.label_obj)
        
        # Reset robot tracking
        self.robots = []
        self.robot_counter = 0
        
        # Clear robot control buttons
        for widget in self.right_panel.winfo_children():
            if isinstance(widget, tk.Frame) and widget not in [self.button_frame, self.history_frame]:
                widget.destroy()
        
        # Recreate the history treeview to ensure it's valid
        self.create_history_treeview()
        
        # Add system message
        self.add_history_entry("System", "Logs cleared and system reset")
        
    def load_nav_graph_file(self):
        """Load navigation graph from JSON file"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
                    level_name = next(iter(data["levels"]))
                    self.nav_graph = data["levels"][level_name]
                self.draw_environment()
                self.move_button.config(state=tk.NORMAL)
                self.add_history_entry("System", "Graph loaded successfully")
            except Exception as e:
                self.add_history_entry("System", f"Error loading file: {e}")

    def draw_environment(self):
        """Draw the navigation graph on canvas"""
        self.canvas.delete("all")
        vertices = self.nav_graph["vertices"]
        lanes = self.nav_graph["lanes"]
        
        # Calculate scaling factors
        self.min_x = min(v[0] for v in vertices)
        self.max_x = max(v[0] for v in vertices)
        self.min_y = min(v[1] for v in vertices)
        self.max_y = max(v[1] for v in vertices)
        
        self.scale_x = (self.canvas.winfo_width() - 2*self.padding) / (self.max_x - self.min_x)
        self.scale_y = (self.canvas.winfo_height() - 2*self.padding) / (self.max_y - self.min_y)
        
        # Draw lanes
        for lane in lanes:
            from_idx, to_idx = lane[0], lane[1]
            from_x, from_y = self._get_canvas_coords(vertices[from_idx])
            to_x, to_y = self._get_canvas_coords(vertices[to_idx])
            self.canvas.create_line(from_x, from_y, to_x, to_y, fill="black", width=2)
        
        # Draw vertices with names
        for idx, vertex in enumerate(vertices):
            x, y = self._get_canvas_coords(vertex)
            color = f"#{random.randint(0, 0xFFFFFF):06x}"
            self.vertex_colors[idx] = color
            
            # Store vertex name (use provided name or generate one)
            vertex_name = vertex[2].get("name", f"V{idx}") if len(vertex) > 2 and isinstance(vertex[2], dict) else f"V{idx}"
            self.vertex_names[idx] = vertex_name
            
            # Draw vertex
            self.canvas.create_oval(x-15, y-15, x+15, y+15, fill=color, outline="black", width=2)
            self.canvas.create_text(x, y-25, text=vertex_name, font=("Arial", 10, "bold"))
            
            # Display additional properties if available
            if len(vertex) > 2 and isinstance(vertex[2], dict):
                props = vertex[2]
                if "type" in props:
                    self.canvas.create_text(x, y+25, text=props["type"], font=("Arial", 8))
        
        # Enable vertex clicking for robot spawning
        self.canvas.bind("<Button-1>", self.on_vertex_click)
    
    def _get_canvas_coords(self, vertex):
        """Convert graph coordinates to canvas coordinates"""
        return (
            self.padding + (vertex[0] - self.min_x) * self.scale_x,
            self.padding + (vertex[1] - self.min_y) * self.scale_y
        )
    
    def on_vertex_click(self, event):
        """Handle vertex clicks to spawn robots"""
        if not self.nav_graph:
            return
            
        # Find closest vertex to click position
        vertices = self.nav_graph["vertices"]
        closest_idx, closest_vertex = min(enumerate(vertices),
                                       key=lambda iv: ((self._get_canvas_coords(iv[1])[0] - event.x)**2 + 
                                                     (self._get_canvas_coords(iv[1])[1] - event.y)**2))
        
        # Spawn new robot
        self.robot_counter += 1
        robot_id = f"R{self.robot_counter}"
        vertex_name = self.vertex_names[closest_idx]
        
        robot = Robot(
            robot_id=robot_id,
            position=closest_vertex,
            canvas=self.canvas,
            vertex_colors=self.vertex_colors,
            padding=self.padding,
            min_x=self.min_x,
            min_y=self.min_y,
            scale_x=self.scale_x,
            scale_y=self.scale_y
        )
        robot.spawn()
        self.robots.append(robot)
        
        # Add to history
        self.add_history_entry(robot_id, f"Spawned at {vertex_name}")
        
        # Create control button for this robot
        btn_frame = tk.Frame(self.right_panel)
        btn_frame.pack(fill=tk.X, pady=2)
        
        tk.Button(btn_frame, text=f"Move {robot_id}", 
                 command=lambda r=robot: self.move_single_robot(r)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text=f"Status {robot_id}", 
                 command=lambda r=robot: self.show_robot_status(r)).pack(side=tk.LEFT, padx=2)
    
    def add_history_entry(self, robot, event):
        """Add an entry to the history log"""
        if not hasattr(self, 'history_tree'):
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            item = self.history_tree.insert("", "end", values=(timestamp, robot, event))
            if self.history_tree.get_children():
                self.history_tree.see(item)
        except tk.TclError:
            # If treeview is invalid, recreate it
            self.create_history_treeview()
            self.add_history_entry(robot, event)
    
    def move_single_robot(self, robot):
        """Move a specific robot to a random vertex"""
        if not self.nav_graph:
            return
            
        next_idx = random.randint(0, len(self.nav_graph["vertices"])-1)
        next_vertex = self.nav_graph["vertices"][next_idx]
        vertex_name = self.vertex_names[next_idx]
        
        robot.move(next_vertex)
        robot.set_status("moving")
        self.add_history_entry(robot.robot_id, f"Moved to {vertex_name}")
    
    def show_robot_status(self, robot):
        """Show detailed status of a robot"""
        status_window = tk.Toplevel(self.master)
        status_window.title(f"Robot {robot.robot_id} Status")
        
        # Find current vertex name
        current_vertex = "Unknown"
        for idx, v in enumerate(self.nav_graph["vertices"]):
            if v[0] == robot.position[0] and v[1] == robot.position[1]:
                current_vertex = self.vertex_names[idx]
                break
        
        status_text = f"""Robot ID: {robot.robot_id}
Current Vertex: {current_vertex}
Status: {robot.get_status()}
Last Action: {robot.last_action}"""
        
        tk.Label(status_window, text=status_text, justify=tk.LEFT).pack(padx=10, pady=10)
        tk.Button(status_window, text="Close", command=status_window.destroy).pack(pady=5)
    
    def move_robots(self):
        """Move all robots to random vertices"""
        if not self.nav_graph:
            return
            
        for robot in self.robots:
            self.move_single_robot(robot)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x750")
    app = FleetManagementApp(root)
    root.mainloop()