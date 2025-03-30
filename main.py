from src.gui.fleet_gui import FleetManagementApp
import tkinter as tk
import cProfile
import cProfile

# In your main code:
if __name__ == "__main__":
    root = tk.Tk()
    app = FleetManagementApp(root)
    
    # Profile the movement
    def profile_movement():
        cProfile.runctx('app.start_movement()', globals(), locals(), 'movement.prof')
    
    # Add a profile button for testing
    tk.Button(app.right_panel, text="Profile", command=profile_movement).pack()
    
    root.mainloop()