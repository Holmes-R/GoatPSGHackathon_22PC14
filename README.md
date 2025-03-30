# GoatPSGHackathon_22PC14

### Project Structure 
![image](https://github.com/user-attachments/assets/df22bd35-cbf2-4665-98f3-4d8b524b29c4)

#### GUI for Testing 

pip install -r requirements.txt

python main.py


### Project Explanation 

#### 1. Visual Representation

##### 1.1 Environment Visualization

    The system provides a clear and interactive visualization of the navigation graph, 
    including vertices (locations) and lanes (paths between locations).

- Vertices 
    - Each vertex is represented as a circular node .
    - Vertices are labeled with unique names .
    - Clicking a vertex allows spawning a robot or assigning a task
- Lanes 
    - Lanes are drawn as lines connecting vertices .
    - Color-coded based on status:

         - Green: Free

        - Yellow: Reserved (in use by a robot)

        -   Red: Blocked (collision or high congestion)

##### 1.1 Robot Visualization
    Robots are visually distinct and update in real-time as they move.

- Each robot is displayed as a colored circle with a unique ID.
- Status Indicators:

        🟢 Moving (Green)

        🟡 Waiting (Yellow)

        🔴 Blocked (Red)

#### 2. Robot Spawing 

##### 2.1 Interactive GUI Spawning

    Users can spawn robots by clicking on any vertex.

- Clicking a vertex opens a popup to spawn a robot .
- Each robot gets a unique ID (e.g., "R1", "R2") .
- If a vertex is occupied, a warning is displayed .

### Project Explanation 

#### 3. Navigation Task Assignment

##### 3.1 Interactive Task Assignment

    Users can assign tasks by selecting a robot and clicking a destination.


- Step 1: Click a robot to select it.

- Step 2: Click a destination vertex.

- The robot immediately computes a path and starts moving.

#### 4. Traffic Negotiation & Collision Avoidance

##### 4.1  Real-Time Traffic Management

    The system ensures robots navigate efficiently without collisions using a combination of reservation-based path planning and priority negotiation algorithms.


-  Path Reservation System ( Two-Phase Commit )

- Congestion-Aware Pathfinding (A* algorithm )

- Priority Negotiation

#### 5. Dynamic Interaction

##### 5.1 Runtime Flexibility

    New robots and tasks can be added without interrupting existing movements.


-  Threaded movement ensures smooth concurrent operations.

- The system dynamically adjusts to new spawns and path changes.
