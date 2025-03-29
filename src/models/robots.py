import random
import time

class Robot:
    def __init__(self, robot_id, node_index, node_color):
        self.robot_id = robot_id
        self.node_index = node_index
        self.node_color = node_color
        self.status = "waiting"  # Initial status
        self.position = node_index  # Position of the robot in the graph
        self.task_complete = False

    def move_to_node(self, new_node_index):
        """Simulate robot movement to a new node."""
        self.status = "moving"
        self.position = new_node_index
        time.sleep(random.uniform(1, 2))  # Simulating movement time
        self.status = "waiting"  # After moving, the robot waits again

    def charge(self):
        """Simulate robot charging."""
        self.status = "charging"
        time.sleep(random.uniform(2, 3))  # Simulating charging time
        self.status = "waiting"  # After charging, the robot waits again

    def complete_task(self):
        """Simulate task completion."""
        self.status = "task complete"
        time.sleep(random.uniform(1, 2))  # Simulating task completion time
        self.status = "waiting"  # After completing a task, robot goes back to waiting

    def update_status(self):
        """Simulate random behavior updates."""
        if self.status == "waiting":
            # Randomly decide whether to move, charge, or complete a task
            action = random.choice(["move", "charge", "task_complete"])
            if action == "move":
                new_node = random.randint(0, 5)  # Random node to move to (change as needed)
                self.move_to_node(new_node)
            elif action == "charge":
                self.charge()
            elif action == "task_complete":
                self.complete_task()

    def get_status(self):
        """Get the current status of the robot."""
        return self.status
