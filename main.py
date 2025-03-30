from src.gui.fleet_gui import FleetManagementApp
import tkinter as tk

def main():
    # Create the main application window
    root = tk.Tk()
    root.title("GOAT Robotics Fleet Management System")
    root.geometry("1200x800")
    
    # Initialize and run the application
    app = FleetManagementApp(root)
    
    # Configure window closing behavior
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()