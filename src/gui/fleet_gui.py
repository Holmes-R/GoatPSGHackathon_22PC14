import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
from datetime import datetime
from src.controllers.fleet_manager import FleetManager

class FleetManagementApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Fleet Management System")
        self.fleet_manager = FleetManager()
        
        # UI Setup
        self.setup_main_window()
        self.setup_ui_components()
        
        # Visualization parameters
        self.padding = 50
        self.vertex_radius = 15
        self.selected_robot = None
        self.after_id = None
        self.canvas.delete("path")
        
    def setup_main_window(self):
        """Configure main window layout"""
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.main_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_panel = tk.Frame(self.main_frame, width=450, bg="#f0f0f0")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

    def setup_ui_components(self):
        """Initialize all UI components"""
        # Control buttons
        self.button_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        self.button_frame.pack(fill=tk.X, pady=10, padx=5)
        
        btn_style = {'width': 20, 'height': 1, 'font': ('Arial', 10)}
        self.load_button = tk.Button(self.button_frame, text="Load Graph", 
                                   command=self.load_nav_graph_file, **btn_style)
        self.load_button.pack(fill=tk.X, pady=3)
        
        self.move_button = tk.Button(self.button_frame, text="Move All Robots", 
                                   command=self.move_robots, state=tk.DISABLED, **btn_style)
        self.move_button.pack(fill=tk.X, pady=3)
        
        self.start_button = tk.Button(self.button_frame, text="Start Movement",
                                   command=self.start_movement, state=tk.DISABLED, **btn_style)
        self.start_button.pack(fill=tk.X, pady=3)
        
        self.clear_button = tk.Button(self.button_frame, text="Clear Logs", 
                                    command=self.clear_logs, **btn_style)
        self.clear_button.pack(fill=tk.X, pady=3)
        
        # History display
        self.setup_history_panel()
        
        # Selection label
        self.selection_label = tk.Label(self.right_panel, 
                                      text="No robot selected", 
                                      font=("Arial", 10),
                                      bg="#f0f0f0")
        self.selection_label.pack(pady=5)

    def setup_history_panel(self):
        """Setup history treeview"""
        ttk.Separator(self.right_panel, orient='horizontal').pack(fill=tk.X, pady=5)
        
        self.history_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        self.history_label = tk.Label(self.history_frame, 
                                    text="ROBOT HISTORY", 
                                    font=("Arial", 12, "bold"),
                                    bg="#f0f0f0")
        self.history_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.history_tree = ttk.Treeview(self.history_frame, 
                                       columns=("Time", "Robot", "Event"), 
                                       show="headings", 
                                       height=20)
        
        # Configure columns and headings
        for col in ("Time", "Robot", "Event"):
            self.history_tree.column(col, width=100 if col != "Event" else 220)
            self.history_tree.heading(col, text=col)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        history_scroll = ttk.Scrollbar(self.history_tree, orient="vertical", 
                                     command=self.history_tree.yview)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=history_scroll.set)

    def load_nav_graph_file(self):
        """Load navigation graph from JSON file"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            success, message = self.fleet_manager.load_nav_graph(file_path)
            if success:
                self.draw_environment()
                self.add_history_entry("System", message)
                self.move_button.config(state=tk.NORMAL)
            else:
                self.add_history_entry("System", message)
    def setup_click_handlers(self):
        """Set up all canvas click handlers"""
        # Clear existing bindings
        self.canvas.tag_unbind("vertex", "<Button-1>")
        self.canvas.unbind("<Button-1>")
        
        # Bind vertex clicks
        if hasattr(self.fleet_manager, 'vertex_names'):
            for idx in self.fleet_manager.vertex_names:
                self.canvas.tag_bind(f"vertex_{idx}", "<Button-1>", 
                                lambda e, idx=idx: self.on_vertex_click(idx))
        
        # Bind general canvas clicks (for robot selection)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
    def draw_environment(self):
        """Draw the navigation graph on canvas"""
        self.canvas.delete("all")
        if not self.fleet_manager.nav_graph:
            return
            
        vertices = self.fleet_manager.nav_graph["vertices"]
        lanes = self.fleet_manager.nav_graph["lanes"]
        
        # Update scaling factors
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.fleet_manager._calculate_scaling_factors(canvas_width, canvas_height)
        
        # Draw lanes
        for lane in lanes:
            from_idx, to_idx = lane[0], lane[1]
            from_x, from_y = self.fleet_manager.get_canvas_coords(vertices[from_idx])
            to_x, to_y = self.fleet_manager.get_canvas_coords(vertices[to_idx])
            self.canvas.create_line(from_x, from_y, to_x, to_y, fill="black", width=2)
        
        # Draw vertices with names and click bindings
        for idx, vertex in enumerate(vertices):
            x, y = self.fleet_manager.get_canvas_coords(vertex)
            color = self.fleet_manager.vertex_colors[idx]
            vertex_name = self.fleet_manager.vertex_names[idx]
            
            # Draw vertex
            vertex_tag = f"vertex_{idx}"
            self.canvas.create_oval(x-10, y-10, x+10, y+10,
                                fill=color, outline="black", width=2,
                                tags=vertex_tag)
            
            # Draw vertex label
            self.canvas.create_text(x, y-25,
                                text=vertex_name,
                                font=("Arial", 10, "bold"))
            
            # Bind click event
            self.canvas.tag_bind(vertex_tag, "<Button-1>",
                            lambda e, idx=idx: self.on_vertex_click(idx))
        
        # Bind general canvas click
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Redraw any existing robots
        for robot in self.fleet_manager.robots:
            if hasattr(robot, 'spawn'):
                robot.spawn()

    def _get_canvas_coords(self, vertex):
        """Convert graph coordinates to canvas coordinates"""
        return (
            self.padding + (vertex[0] - self.fleet_manager.min_x) * self.fleet_manager.scale_x,
            self.padding + (vertex[1] - self.fleet_manager.min_y) * self.fleet_manager.scale_y
        )

    def on_vertex_click(self, vertex_idx):
        """Handle vertex clicks to spawn robots"""
        if not self.fleet_manager.nav_graph:
            return
            
        # Spawn new robot at clicked vertex
        robot, message = self.fleet_manager.spawn_robot(vertex_idx, self.canvas)
        if robot:
            self.add_history_entry(robot.robot_id, message)
            self.prompt_destination(robot)
            self.start_button.config(state=tk.NORMAL)

    def prompt_destination(self, robot):
        """Prompt user to select destination for a robot"""
        dest_window = tk.Toplevel(self.master)
        dest_window.title(f"Select Destination for {robot.robot_id}")
        
        tk.Label(dest_window, text="Select destination vertex:").pack(pady=5)
        
        vertex_listbox = tk.Listbox(dest_window, height=10, width=30)
        current_idx = self.fleet_manager.get_vertex_index(robot.position)
        
        # Add all other vertices to listbox
        for idx, name in sorted(self.fleet_manager.vertex_names.items()):
            if idx != current_idx:
                vertex_listbox.insert(tk.END, name)
        
        vertex_listbox.pack(pady=5)
        
        def assign_destination():
            selection = vertex_listbox.curselection()
            if selection:
                selected_name = vertex_listbox.get(selection)
                vertex_idx = next(idx for idx, name in self.fleet_manager.vertex_names.items() 
                                 if name == selected_name)
                
                success, message = self.fleet_manager.set_robot_destination(robot.robot_id, vertex_idx)
                self.add_history_entry(robot.robot_id, message)
                if success:
                    self.start_button.config(state=tk.NORMAL)
                dest_window.destroy()
        
        tk.Button(dest_window, text="Assign Destination", 
                 command=assign_destination).pack(pady=5)

    def update_robot_display(self, robot):
        """Callback for updating robot visualization"""
        robot.update_visualization()
        self.master.update()  # Refresh GUI
    
    def start_movement(self):
        """Start animated movement"""
        if self.after_id:
            self.master.after_cancel(self.after_id)
        
        success, messages = self.fleet_manager.start_movement(self.update_robot_display)
        for msg in messages:
            self.add_history_entry("System", msg)
        
        if success:
            self.start_button.config(state=tk.DISABLED)

        def on_closing(self):
            """Handle window closing"""
            if self.after_id:
                self.master.after_cancel(self.after_id)
            self.master.destroy()

    def move_robots(self):
        """Move all robots to random vertices"""
        success, messages = self.fleet_manager.move_all_robots_randomly()
        for msg in messages:
            self.add_history_entry("System", msg)
        
        if success:
            # Update robot positions on canvas
            for robot in self.fleet_manager.robots:
                x, y = self._get_canvas_coords(robot.position)
                self.canvas.coords(robot.robot_obj, x-10, y-10, x+10, y+10)
                self.canvas.coords(robot.label_obj, x, y-15)

    def on_canvas_click(self, event):
        """Handle canvas clicks for robot selection"""
        clicked_pos = (
            (event.x - self.padding) / self.fleet_manager.scale_x + self.fleet_manager.min_x,
            (event.y - self.padding) / self.fleet_manager.scale_y + self.fleet_manager.min_y
        )
        
        robot = self.fleet_manager.select_robot(clicked_pos)
        if robot:
            self.selected_robot = robot
            self.selection_label.config(text=f"Selected: {robot.robot_id}")
            
            # Highlight selected robot
            x, y = self._get_canvas_coords(robot.position)
            self.canvas.delete("selection_highlight")
            self.canvas.create_oval(x-15, y-15, x+15, y+15,
                                   outline="red", width=3,
                                   tags="selection_highlight")
        else:
            self.deselect_robot()

    def deselect_robot(self):
        """Deselect the currently selected robot"""
        self.selected_robot = None
        self.selection_label.config(text="No robot selected")
        self.canvas.delete("selection_highlight")

    def add_history_entry(self, robot, event):
        """Add an entry to the history log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = self.history_tree.insert("", "end", values=(timestamp, robot, event))
        self.history_tree.see(item)

    def clear_logs(self):
        """Clear all logs and reset the system"""
        if messagebox.askyesno("Confirm Clear", "Clear all logs and reset system?"):
            self.canvas.delete("all")
            message = self.fleet_manager.clear_all()
            self.history_tree.delete(*self.history_tree.get_children())
            self.add_history_entry("System", message)
            self.move_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.deselect_robot()

    

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    app = FleetManagementApp(root)
    root.mainloop()