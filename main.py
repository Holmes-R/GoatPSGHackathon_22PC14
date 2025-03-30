from src.gui.fleet_gui import FleetManagementApp
import tkinter as tk
import cProfile

def main():
    # Create the main application window
    root = tk.Tk()
    root.title("GOAT Robotics Fleet Management System")
    root.geometry("1200x800")
    
    # Initialize and run the application
    app = FleetManagementApp(root)
    
    # Configure window closing behavior
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    def profile_movement():
        cProfile.runctx('app.start_movement()', globals(), locals(), 'movement.prof')
    
    # Add a profile button for testing
    tk.Button(app.right_panel, text="Profile", command=profile_movement).pack()
    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()