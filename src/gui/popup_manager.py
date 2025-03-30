import tkinter as tk
from tkinter import messagebox

class PopupManager:
    @staticmethod
    def show_occupancy_error(parent, vertex_name, robot_id, find_nearest_callback=None):
        """Show 'Destination Occupied' pop-up."""
        msg = f"Destination Occupied\n{vertex_name} is taken by Robot {robot_id}.\nPlease choose another location."
        
        if find_nearest_callback:
            dialog = tk.Toplevel(parent)
            dialog.title("Conflict Detected")
            
            tk.Label(dialog, text=msg).pack(pady=10)
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=5)
            
            tk.Button(button_frame, text="OK", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Find Nearest", command=find_nearest_callback).pack(side=tk.LEFT)
        else:
            messagebox.showerror("Destination Occupied", msg)