# GoatPSGHackathon_22PC14

### Project Structure 
![image](https://github.com/user-attachments/assets/df22bd35-cbf2-4665-98f3-4d8b524b29c4)

#### GUI for Testing 

To run tests, run the following command 

```bash
  pip install -r requirements.txt 
  python main.py
```
####

### Project Explanation 

![image](https://github.com/user-attachments/assets/ae0e0d44-2fce-48d5-9ce2-60fde1be33d0)

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

![image](https://github.com/user-attachments/assets/2f816361-80ea-41ce-97e9-4845767cd11b)

#### 2. Robot Spawing 

##### 2.1 Interactive GUI Spawning

    Users can spawn robots by clicking on any vertex.

- Clicking a vertex opens a popup to spawn a robot .
- Each robot gets a unique ID (e.g., "R1", "R2") .
- If a vertex is occupied, a warning is displayed .

![image](https://github.com/user-attachments/assets/81e974a4-4d71-4022-adae-22195a8259d4)


#### 3. Navigation Task Assignment

##### 3.1 Interactive Task Assignment

    Users can assign tasks by selecting a robot and clicking a destination.


- Step 1: Click a robot to select it.

- Step 2: Click a destination vertex.

- The robot immediately computes a path and starts moving.

- Primary Algorithm: A (A-Star) with Congestion Awareness

- Fallback Algorithm: Breadth-First Search (BFS) : Finds any available path

  ![image](https://github.com/user-attachments/assets/ad94e0cb-6185-4a8d-b593-c438bfdc5abe)


#### 4. Traffic Negotiation & Collision Avoidance

##### 4.1  Real-Time Traffic Management

    The system ensures robots navigate efficiently without collisions using a combination of reservation-based path planning and priority negotiation algorithms.


-  Path Reservation System ( Two-Phase Commit )

- Congestion-Aware Pathfinding (A* algorithm )

- Priority Negotiation

![image](https://github.com/user-attachments/assets/b1dbf0aa-f5aa-4588-9b61-986817760f2b)

#### 5. Dynamic Interaction

##### 5.1 Runtime Flexibility

    New robots and tasks can be added without interrupting existing movements.


-  Threaded movement ensures smooth concurrent operations.

- The system dynamically adjusts to new spawns and path changes.

![image](https://github.com/user-attachments/assets/b63d5f0c-3316-4fbd-bc94-405d53434f99)


#### 6. Occupancy and Conflict Notifications

##### 6.1 User Alerts

    The system warns users when a path is blocked.


-  Visual cues (flashing red) for conflicts.

![image](https://github.com/user-attachments/assets/111268e1-3f31-49c4-a956-24e2c4b35f61)

#### 7. Logging & Monitoring

##### 7.1 Detailed Logging

    All robot activities are logged for tracking.

-  Log File: robot_<ROBOT_ID>.log records:

    - Spawn events
    - Robot ID 
    - Action 
    - Path 
    - Status 
    - Battery Life 

- GUI Log Panel: Real-time updates in a scrollable history.
- Log File Image 
- ![image](https://github.com/user-attachments/assets/00614519-4dd6-4b10-b881-52a1d7c480b3)

###  Important Libraries Used 

- Tkinder
- os 
- threading 
- time 
- heapq
