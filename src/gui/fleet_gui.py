import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
from collections import deque
import threading
import math
import random
from src.controllers.fleet_manager import FleetManager
import time 
class FleetManagementApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Fleet Management System")
        self.fleet_manager = FleetManager()
        self.threads = []
        self.status_colors = {
            "moving": "green",
            "waiting": "yellow",
            "blocked": "red",
            "idle": "blue",
            "charging": "purple",
            "error": "orange"
        }
        
        self.setup_main_window()
        self.setup_ui_components()
        self.setup_status_legend_lane()
        self.setup_status_legend_vertex()
        self.padding = 50
        self.vertex_radius = 15
        self.selected_robot = None
        self.after_id = None
        self.canvas.delete("path")
        self.vertex_occupancy = {}  
        self.setup_vertex_occupancy_tracker()
        self.initialize_core_components()
        self.initialize_state()

    def initialize_core_components(self):
        self.fleet_manager = FleetManager()
        self.threads = []
    
    def initialize_state(self):
        self.padding = 50
        self.vertex_radius = 15
        self.selected_robot = None
        self.after_id = None
        self.vertex_occupancy = {}  
        self.setup_vertex_occupancy_tracker()


    def setup_main_window(self):
        """ Creates the main canvas and right panel """
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.main_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_panel = tk.Frame(self.main_frame, width=300, bg="#f0f0f0")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10,pady=10)

    def setup_status_legend_lane(self):
        """Creates visual legends for status indicators"""
        legend_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        legend_frame.pack(fill=tk.X, pady=10, padx=5,)
        
        tk.Label(legend_frame, text="Lane Status Legend:", 
                font=("Arial", 10, "bold"), bg="#f0f0f0").pack(anchor=tk.W)
                
        for text, color in [
            ("Free", self.status_colors["moving"]),
            ("Lane in Use", self.status_colors["waiting"]),
            ("Blocked", self.status_colors["blocked"]),
            ("Error", self.status_colors["error"])
        ]:
            frame = tk.Frame(legend_frame, bg="#f0f0f0")
            frame.pack(fill=tk.X, pady=5,padx=5)
            
            canvas = tk.Canvas(frame, width=20, height=20, bg="#f0f0f0", 
                             highlightthickness=0)
            canvas.pack(side=tk.LEFT)
            canvas.create_oval(2, 2, 18, 18, fill=color, outline="black")
            
            tk.Label(frame, text=text, bg="#f0f0f0").pack(side=tk.LEFT, padx=5)

    def setup_ui_components(self):
        """Sets up buttons, history panel, and selection label"""
        self.button_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        self.button_frame.pack(fill=tk.X, pady=10, padx=5)
        
        btn_style = {'width': 25, 'height': 2, 'font': ('Arial', 10)}
        tk.Button(self.button_frame, text="Load Graph", 
                 command=self.load_nav_graph_file, **btn_style).pack(fill=tk.X, pady=3)
        
        self.start_button = tk.Button(self.button_frame, text="Start Movement",
                                   command=self.start_movement, state=tk.DISABLED, **btn_style)
        self.start_button.pack(fill=tk.X, pady=5)
        tk.Button(self.button_frame, text="Clear Logs", 
                command=self.clear_logs, **btn_style).pack(fill=tk.X, pady=5)
        
        self.setup_history_panel()
        
        self.selection_label = tk.Label(self.right_panel, 
                                      text="No robot selected", 
                                      font=("Arial", 11),
                                      width=30,
                                      bg="#f0f0f0")
        self.selection_label.pack(pady=10)

    def setup_history_panel(self):
        ttk.Separator(self.right_panel, orient='horizontal').pack(fill=tk.X, pady=5)
        
        self.history_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(self.history_frame, text="ROBOT HISTORY", 
                font=("Arial", 12, "bold"), bg="#f0f0f0").pack(anchor=tk.W, pady=(0, 5))
        
        self.history_tree = ttk.Treeview(self.history_frame, 
                                       columns=("Time", "Robot", "Event"), 
                                       show="headings", 
                                       height=20)
        
        for col in ("Time", "Robot", "Event"):
            self.history_tree.column(col, width=100 if col != "Event" else 260)
            self.history_tree.heading(col, text=col)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        history_scroll = ttk.Scrollbar(self.history_tree, orient="vertical", 
                                     command=self.history_tree.yview)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.configure(yscrollcommand=history_scroll.set)

    def setup_status_legend_vertex(self):
        """Creates visual legends for status indicators"""
        legend_frame = tk.Frame(self.right_panel, bg="#f0f0f0")
        legend_frame.pack(fill=tk.X, pady=10, padx=5)

        tk.Label(legend_frame, 
                text="Robot Status Legend:", 
                font=("Arial", 10, "bold"), 
                bg="#f0f0f0").pack(anchor=tk.W)

        status_items = [
            ("Move / Task Completed", "green", "→"),      
            ("Waiting", "yellow", "⏸"),              
            ("Error/Blocked", "red", "⚠️")            
        ]

        for text, color, symbol in status_items:
            item_frame = tk.Frame(legend_frame, bg="#f0f0f0")
            item_frame.pack(fill=tk.X, pady=2, padx=5)

            icon_canvas = tk.Canvas(item_frame, width=24, height=24, 
                                bg="#f0f0f0", highlightthickness=0)
            icon_canvas.pack(side=tk.LEFT)
            icon_canvas.create_oval(4, 4, 20, 20, fill=color, outline="black")
            icon_canvas.create_text(12, 12, text=symbol, font=("Arial", 10))

          
            tk.Label(item_frame, text=text, bg="#f0f0f0", 
                    font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
    
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
    
   ### CORE OPERATIONS 
 
    def load_nav_graph_file(self):
        """ Loads navigation graph from JSON file using FleetManager"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            success, message = self.fleet_manager.load_nav_graph(file_path)
            if success:
                self.setup_vertex_occupancy_tracker() 
                self.draw_environment()
                self.add_history_entry("System", message)
            else:
                self.add_history_entry("System", message)

    def draw_environment(self):
        """Draw the navigation graph with updated occupancy status"""
        self.canvas.delete("all")
        if not self.fleet_manager.nav_graph:
            return
            
        self.update_vertex_occupancy()  
        FREE_COLOR = "#00aa00"   
        IN_USE_COLOR = "#ffcc00" 
        DEFAULT_COLOR = "#cccccc"
        vertices = self.fleet_manager.nav_graph["vertices"]
        lanes = self.fleet_manager.nav_graph["lanes"]
        
        for lane in lanes:
            from_idx, to_idx = lane[0], lane[1]
            from_x, from_y = self.fleet_manager.get_canvas_coords(vertices[from_idx])
            to_x, to_y = self.fleet_manager.get_canvas_coords(vertices[to_idx])
            
            lane_key = (min(from_idx, to_idx), max(from_idx, to_idx))
            lane_tag = f"lane_{lane_key[0]}_{lane_key[1]}"
            
            is_reserved = hasattr(self.fleet_manager, 'traffic_manager') and \
                        lane_key in self.fleet_manager.traffic_manager.lane_reservations
            
            color = IN_USE_COLOR if is_reserved else FREE_COLOR
            
            self.canvas.create_line(from_x, from_y, to_x, to_y,
                                width=3, fill=color, tags=lane_tag)
        
        for idx, vertex in enumerate(vertices):
            x, y = self.fleet_manager.get_canvas_coords(vertex)
            base_color = self.fleet_manager.vertex_colors.get(idx, "#888888")
            vertex_name = self.fleet_manager.vertex_names.get(idx, f"V{idx}")
            
            if self.vertex_occupancy.get(idx):
                self.canvas.create_oval(x-12, y-12, x+12, y+12,
                                      fill=base_color, outline="red", width=3,
                                      tags=f"vertex_{idx}")
            else:
                self.canvas.create_oval(x-10, y-10, x+10, y+10,
                                      fill=base_color, outline="black", width=2,
                                      tags=f"vertex_{idx}")
            
            self.canvas.create_text(x, y-25, text=vertex_name,
                                  font=("Arial", 10, "bold"),
                                  tags=f"label_{idx}")
            
            self.canvas.tag_bind(f"vertex_{idx}", "<Button-1>",
                               lambda e, idx=idx: self.on_vertex_click(idx))
        
        for robot in self.fleet_manager.robots:
            if hasattr(robot, 'spawn'):
                robot.spawn()

    def on_vertex_click(self, vertex_idx):
        """ Handles vertex selection for robot spawning """
        if not self.fleet_manager.nav_graph:
            return
            
        self.update_vertex_occupancy()
        occupying_robot = self.vertex_occupancy.get(vertex_idx)
        
        if occupying_robot:
            vertex_name = self.fleet_manager.vertex_names.get(vertex_idx, f"Vertex {vertex_idx}")
            self.show_occupancy_popup(vertex_idx, vertex_name, occupying_robot)
            return
            
        robot, message = self.fleet_manager.spawn_robot(vertex_idx, self.canvas)
        if robot:
            self.update_vertex_occupancy() 
            self.add_history_entry(robot.robot_id, message)
            self.prompt_destination(robot)
            self.start_button.config(state=tk.NORMAL)
        else:
            self.add_history_entry("System", message)
    
    def prompt_destination(self, robot):
        """Shows dialog for selecting robot destinations """
        dest_window = tk.Toplevel(self.master)
        dest_window.title(f"Select Destination for {robot.robot_id}")
        
        main_frame = tk.Frame(dest_window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="Select destination vertex:").pack(anchor=tk.W)
        
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dest_listbox = tk.Listbox(list_frame, height=10, width=40,
                                     yscrollcommand=scrollbar.set, selectmode=tk.SINGLE)
        self.dest_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.dest_listbox.yview)
        
        current_idx = self.fleet_manager.get_vertex_index(robot.position)
        for idx, name in sorted(self.fleet_manager.vertex_names.items()):
            if idx != current_idx:
                occupied_by = self._get_vertex_occupant(idx)
                display_text = f"{name}{' (Occupied)' if occupied_by else ''}"
                self.dest_listbox.insert(tk.END, display_text)
                if occupied_by:
                    self.dest_listbox.itemconfig(tk.END, {'fg': 'red', 'bg': '#FFDDDD'})
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(button_frame, text="Find Nearest Available",
                 command=lambda: self.find_nearest_available(robot, current_idx, dest_window),
                 width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Assign Destination",
                 command=lambda: self.assign_selected_destination(robot, dest_window),
                 width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel",
                 command=dest_window.destroy, width=20).pack(side=tk.RIGHT, padx=5)
        
    def start_movement(self):
        """Start concurrent movement of all robots"""
        self.canvas.delete("status_*")  
        
        self.highlight_collisions()
        
        threads = []
        for robot in self.fleet_manager.robots:
            if robot.robot_id in self.fleet_manager.robot_destinations:
                target = self.fleet_manager.robot_destinations[robot.robot_id]
                t = threading.Thread(
                    target=self.fleet_manager.move_robot_concurrently,
                    args=(robot, target, self.safe_gui_update),
                    daemon=True
                )
                threads.append(t)
                t.start()
        
        self.threads = threads
        self.add_history_entry("System", "Started concurrent movement")

    def assign_selected_destination(self, robot, window):
        """ Assigns a selected destination to a robot after validation """
        selection = self.dest_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a destination vertex")
            return
        
        selected_text = self.dest_listbox.get(selection[0])
        selected_name = selected_text.split(' (Occupied)')[0].strip()
        
        vertex_idx = None
        for idx, name in self.fleet_manager.vertex_names.items():
            if name == selected_name:
                vertex_idx = idx
                break
        
        if vertex_idx is None:
            messagebox.showerror("Error", "Selected vertex not found")
            return
        
        occupying_robot = self._get_vertex_occupant(vertex_idx)
        if occupying_robot:
            self.show_vertex_conflict(vertex_idx)
            
            conflict_popup = tk.Toplevel(window)
            conflict_popup.title("Destination Occupied")
            
            msg = (f"Vertex '{selected_name}' is occupied by Robot {occupying_robot}\n"
                f"Please select a different destination.")
            tk.Label(conflict_popup, text=msg, padx=20, pady=20).pack()
            
            for r in self.fleet_manager.robots:
                if r.robot_id == occupying_robot:
                    self.highlight_robot(r)
                    break
            
            tk.Button(conflict_popup, text="OK", command=conflict_popup.destroy).pack(pady=10)
            return
        
        success, message = self.fleet_manager.set_robot_destination(robot.robot_id, vertex_idx)
        self.add_history_entry(robot.robot_id, message)
        if success:
            self.start_button.config(state=tk.NORMAL)
        window.destroy()

    def show_vertex_conflict(self, vertex_idx):
        """Visual indicator for vertex conflicts"""
        if not hasattr(self.fleet_manager, 'nav_graph') or vertex_idx >= len(self.fleet_manager.nav_graph["vertices"]):
            return
        
        vertex = self.fleet_manager.nav_graph["vertices"][vertex_idx]
        x, y = self.fleet_manager.get_canvas_coords(vertex)
        
        self.canvas.delete("dest_conflict")
        self.canvas.create_oval(x-15, y-15, x+15, y+15,
                            outline="red", width=3,
                            tags="dest_conflict")
        
        def pulse():
            try:
                current_width = float(self.canvas.itemcget("dest_conflict", "width"))
                new_width = 3.0 if current_width < 3.0 else 5.0
                self.canvas.itemconfig("dest_conflict", width=new_width)
                self.master.after(300, pulse)
            except:
                pass
        
        pulse()
        self.master.after(3000, lambda: self.canvas.delete("dest_conflict"))

    def highlight_vertex(self, vertex_idx):
        """Visual feedback methods"""
        self.canvas.delete("vertex_highlight")
        
        if not self.fleet_manager.nav_graph or vertex_idx >= len(self.fleet_manager.nav_graph["vertices"]):
            return
        
        vertex = self.fleet_manager.nav_graph["vertices"][vertex_idx]
        x, y = self.fleet_manager.get_canvas_coords(vertex)
        
        self.canvas.create_oval(x-15, y-15, x+15, y+15,
                              outline="yellow", width=3,
                              tags="vertex_highlight")
        
        def blink():
            current_color = self.canvas.itemcget("vertex_highlight", "outline")
            new_color = "yellow" if current_color == "" else ""
            self.canvas.itemconfig("vertex_highlight", outline=new_color)
            self.master.after(500, blink)
        
        blink()

    def highlight_robot(self, robot):
        """Visual feedback methods"""
        x, y = self.fleet_manager.get_canvas_coords(robot.position)
        self.canvas.delete("robot_highlight")
        
        self.canvas.create_oval(x-20, y-20, x+20, y+20,
                            outline="orange", width=3.0,
                            tags="robot_highlight")
        
        def pulse_robot():
            try:
                current = self.canvas.itemcget("robot_highlight", "outline")
                new_color = "orange" if current == "" else ""
                self.canvas.itemconfig("robot_highlight", outline=new_color)
                self.master.after(500, pulse_robot)
            except:
                pass
        
        pulse_robot()
        self.master.after(5000, lambda: self.canvas.delete("robot_highlight"))
    
    ### ROBOT MANAGEMENT    

    def update_vertex_occupancy(self):
        """Update which robots occupy which vertices"""
        for vertex_idx in self.vertex_occupancy:
            self.vertex_occupancy[vertex_idx] = None
        
        for robot in self.fleet_manager.robots:
            vertex_idx = self.fleet_manager.get_vertex_index(robot.position)
            if vertex_idx != -1:
                self.vertex_occupancy[vertex_idx] = robot.robot_id

    def update_robot_display(self, robot):
        """Update robot visualization with offset for multiple robots at the same vertex"""
        if robot.status == "idle":
            color = "#808080"  
            self.canvas.itemconfig(robot.gui_id, fill=color)
            self.status_tree.item(robot.robot_id, values=(robot.robot_id, "IDLE AT DESTINATION"))
        x, y = self._get_canvas_coords(robot.position)
        
        same_pos_robots = [r for r in self.fleet_manager.robots 
                        if r.position == robot.position]
        
        index = same_pos_robots.index(robot)
        
        radius = 15
        angle = index * (2 * 3.14159 / 6)  
        offset_x = radius * math.cos(angle)
        offset_y = radius * math.sin(angle)
        
        if not hasattr(robot, 'gui_id'):
            robot.gui_id = self.canvas.create_oval(
                x-10+offset_x, y-10+offset_y,
                x+10+offset_x, y+10+offset_y,
                fill=self.status_colors.get(robot.status, "blue"),
                tags="robot"
            )
            robot.label_id = self.canvas.create_text(
                x+offset_x, y+offset_y-15,
                text=robot.robot_id,
                font=("Arial", 8)
            )
        else:
            self.canvas.coords(
                robot.gui_id,
                x-10+offset_x, y-10+offset_y,
                x+10+offset_x, y+10+offset_y
            )
            self.canvas.coords(
                robot.label_id,
                x+offset_x, y+offset_y-15
            )
            self.canvas.itemconfig(robot.gui_id, fill=self.status_colors.get(robot.status, "blue"))
        
        self.master.update()


    def setup_vertex_occupancy_tracker(self):
        """Initialize vertex occupancy tracking"""
        self.vertex_occupancy = {}  
        
        if (hasattr(self.fleet_manager, 'nav_graph')) and self.fleet_manager.nav_graph:
            self.vertex_occupancy = {
                idx: None for idx in range(len(self.fleet_manager.nav_graph["vertices"]))
            }
    
    def safe_gui_update(self, robot, status):
        """Thread-safe GUI update that also updates occupancy"""
        def update():
            robot.status = status
            robot.update_visualization()
            
            self.draw_environment()
            
            for r in self.fleet_manager.robots:
                r.update_visualization()

            x, y = self.fleet_manager.get_canvas_coords(robot.position)
            self.canvas.delete(f"status_{robot.robot_id}")
            
            if status == "waiting":
                self.canvas.create_oval(
                    x-15, y-15, x+15, y+15,
                    outline="#FFFF00", width=2, dash=(5,2),
                    tags=f"status_{robot.robot_id}"
                )
            elif status == "blocked":
                self.canvas.create_oval(
                    x-15, y-15, x+15, y+15,
                    outline="#FF0000", width=3,
                    tags=f"status_{robot.robot_id}"
                )
            elif status == "moving":
                self.canvas.create_line(
                    x, y, x+20, y,
                    arrow=tk.LAST, fill="#00FF00", width=2,
                    tags=f"status_{robot.robot_id}"
                )
        
        self.master.after(0, update)

    def _get_vertex_occupant(self, vertex_idx):
        if not hasattr(self.fleet_manager, 'nav_graph'):
            return None
            
        for robot in self.fleet_manager.robots:
            if self.fleet_manager.get_vertex_index(robot.position) == vertex_idx:
                return robot.robot_id
        return None

    def move_robot_concurrently(self, robot, target_pos, gui_update_callback):
        """Handles robot movement logic with collision avoidance"""
        try:
            while True:
                self.update_vertex_occupancy()
                
                if self.has_reached_destination(robot.position, target_pos):
                    robot.set_status("idle")
                    gui_update_callback(robot, "idle")
                    self.mark_complete_path_green(robot)
                    if hasattr(self.fleet_manager, 'traffic_manager'):
                        self.fleet_manager.traffic_manager.release_all_for_robot(robot.robot_id)
                    break
                    
                path_indices = self.find_path_to_destination(robot.position, target_pos)
                if not path_indices:
                    robot.set_status("blocked")
                    gui_update_callback(robot, "blocked")
                    time.sleep(1)
                    continue
                    
                robot.path_history.extend(path_indices)
                
                if not self.fleet_manager.traffic_manager.reserve_path(robot.robot_id, path_indices):
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
    
    ### Helper Functions
    
    def find_nearest_available_vertex(self, start_vertex_idx):
        """Uses BFS to find closest unoccupied vertex"""
        if not hasattr(self.fleet_manager, 'nav_graph'):
            return -1
            
        vertices = self.fleet_manager.nav_graph["vertices"]
        lanes = self.fleet_manager.nav_graph["lanes"]
        num_vertices = len(vertices)
        
        adj = [[] for _ in range(num_vertices)]
        for lane in lanes:
            from_idx, to_idx = lane[0], lane[1]
            adj[from_idx].append(to_idx)
            adj[to_idx].append(from_idx)
        
        visited = [False] * num_vertices
        queue = deque([start_vertex_idx])
        visited[start_vertex_idx] = True
        
        while queue:
            current_idx = queue.popleft()
            
            for neighbor_idx in adj[current_idx]:
                if not visited[neighbor_idx]:
                    if not self._get_vertex_occupant(neighbor_idx):
                        return neighbor_idx
                        
                    visited[neighbor_idx] = True
                    queue.append(neighbor_idx)
        
        return -1

    def find_nearest_available(self, robot, current_idx, window):
        nearest_idx = self.find_nearest_available_vertex(current_idx)
        if nearest_idx != -1:
            nearest_name = self.fleet_manager.vertex_names[nearest_idx]
            for i in range(self.dest_listbox.size()):
                if self.dest_listbox.get(i).startswith(nearest_name):
                    self.dest_listbox.selection_clear(0, tk.END)
                    self.dest_listbox.selection_set(i)
                    self.dest_listbox.see(i)
                    self.highlight_vertex(nearest_idx)
                    break

    def show_occupancy_popup(self, vertex_idx, vertex_name, occupied_by, parent_window=None):
        """Displays conflict information"""
        popup = tk.Toplevel(parent_window or self.master)
        popup.title("Destination Occupied")
        popup.geometry("450x250")
        
        msg = (f"The selected vertex {vertex_name} is already occupied by Robot {occupied_by}.\n\n"
               "Please choose another location.")
        tk.Label(popup, text=msg, wraplength=400, justify=tk.LEFT).pack(pady=20)
        
        button_frame = tk.Frame(popup)
        button_frame.pack(pady=10)
        
        def find_and_highlight():
            nearest_idx = self.find_nearest_available_vertex(vertex_idx)
            if nearest_idx != -1:
                self.highlight_vertex(nearest_idx)
                popup.destroy()
        
        tk.Button(button_frame, text="OK", command=popup.destroy).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Find Nearest", command=find_and_highlight).pack(side=tk.LEFT)

    def mark_complete_path_green(self, robot):
        """Mark all lanes in robot's path history as green when done"""
        if not hasattr(robot, 'path_history') or not robot.path_history:
            return
            
        unique_lanes = set()
        for i in range(len(robot.path_history)-1):
            from_idx = robot.path_history[i]
            to_idx = robot.path_history[i+1]
            unique_lanes.add((min(from_idx, to_idx), max(from_idx, to_idx)))
        
        for lane in unique_lanes:
            lane_tag = f"lane_{lane[0]}_{lane[1]}"
            self.canvas.itemconfig(lane_tag, fill="#00aa00")  
        
        robot.path_history = []

    def on_closing(self):
        """Clean up when window closes"""
        for t in self.threads:
            t.join(timeout=0.1)
        self.master.destroy()

    ### LOGS 

    def add_history_entry(self, robot, event):
        """Add an entry to the history log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = self.history_tree.insert("", "end", values=(timestamp, robot, event))
        self.history_tree.see(item)

    ### Status Management
    
    def update_robot_status(self, robot, status):
        """Update robot visualization."""
        x, y = self.fleet_manager.get_canvas_coords(robot.position)
        color = self.status_colors[status]
        
        if not hasattr(robot, 'gui_id'):
            robot.gui_id = self.canvas.create_oval(x-10, y-10, x+10, y+10, fill=color)
        else:
            self.canvas.itemconfig(robot.gui_id, fill=color)
            self.canvas.coords(robot.gui_id, x-10, y-10, x+10, y+10)
        
        for item in self.status_tree.get_children():
            if self.status_tree.item(item, "values")[0] == robot.robot_id:
                self.status_tree.item(item, values=(robot.robot_id, status))
                break
        else:
            self.status_tree.insert("", "end", values=(robot.robot_id, status))
 
    ### DYNAMIC CONTROLS 
    
    def setup_dynamic_controls(self):
        """Add runtime control buttons"""
        control_frame = tk.Frame(self.right_panel)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Spawn Robot", 
                command=self.spawn_robot_at_random).pack(pady=5)
        
        self.robot_var = tk.StringVar()
        tk.OptionMenu(control_frame, self.robot_var, *[r.robot_id for r in self.fleet_manager.robots]).pack()
        tk.Button(control_frame, text="Assign New Task", 
                command=self.assign_new_task).pack(pady=5)

    def spawn_robot_at_random(self):
        """Spawn robot at random vertex"""
        if self.fleet_manager.nav_graph:
            idx = random.randint(0, len(self.fleet_manager.nav_graph["vertices"])-1)
            self.fleet_manager.spawn_robot_threadsafe(idx, self.canvas)

    def assign_new_task(self):
        """Assign task to selected robot"""
        robot_id = self.robot_var.get()
        if robot_id and self.fleet_manager.nav_graph:
            idx = random.randint(0, len(self.fleet_manager.nav_graph["vertices"])-1)
            self.fleet_manager.task_manager.add_task(robot_id, 
                self.fleet_manager.nav_graph["vertices"][idx])
    
    ### UTILITY FUNCTION 

    def _get_canvas_coords(self, vertex):
        """Convert graph coordinates to canvas coordinates"""
        return (
            self.padding + (vertex[0] - self.fleet_manager.min_x) * self.fleet_manager.scale_x,
            self.padding + (vertex[1] - self.fleet_manager.min_y) * self.fleet_manager.scale_y
        )

    def highlight_collisions(self):
        """Highlight any detected collisions between robots"""
        robot_positions = {robot.robot_id: robot.position for robot in self.fleet_manager.robots}
        collisions = self.fleet_manager.traffic_manager.detect_collision(robot_positions)
        
        self.canvas.delete("collision_highlight")
        
        for robot1_id, robot2_id in collisions:
            robot1 = next(r for r in self.fleet_manager.robots if r.robot_id == robot1_id)
            robot2 = next(r for r in self.fleet_manager.robots if r.robot_id == robot2_id)
            
            x1, y1 = self._get_canvas_coords(robot1.position)
            x2, y2 = self._get_canvas_coords(robot2.position)
            
            self.canvas.create_line(x1, y1, x2, y2, 
                                fill="red", width=2, dash=(5,2),
                                tags="collision_highlight")
            
            self.canvas.create_oval(x1-15, y1-15, x1+15, y1+15,
                                outline="red", width=3,
                                tags="collision_highlight")
            self.canvas.create_oval(x2-15, y2-15, x2+15, y2+15,
                                outline="red", width=3,
                                tags="collision_highlight")
            

    def update_lane_color(self, lane, color):
        """Update the visual representation of a lane"""
        if not hasattr(self.fleet_manager, 'nav_graph'):
            return
            
        vertices = self.fleet_manager.nav_graph["vertices"]
        from_idx, to_idx = lane
        
        from_x, from_y = self.fleet_manager.get_canvas_coords(vertices[from_idx])
        to_x, to_y = self.fleet_manager.get_canvas_coords(vertices[to_idx])
        
        lane_tag = f"lane_{from_idx}_{to_idx}"
        self.canvas.delete(lane_tag)
        self.canvas.create_line(from_x, from_y, to_x, to_y,
                            width=3, fill=color, tags=lane_tag)

