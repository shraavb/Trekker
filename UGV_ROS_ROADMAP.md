# UGV Beast - Construction Inspection Rover

An autonomous site inspection rover built on the UGV Beast platform. The system combines GPS-fused localization via EKF, visual SLAM for environment mapping, Nav2 geofenced autonomous navigation, and a YOLOv8 + VLM hazard detection pipeline with position-tagged anomaly logging streamed to a remote supervisory dashboard.

---

## Starting Point

From existing background: LeRobot = manipulation/pick-and-place, Isaac Sim = simulation, ego4d = offline video RL.

**What's new with the UGV:**
- Mobile robot navigation (vs. fixed-arm manipulation)
- Hardware-in-the-loop (real serial UART ↔ ESP32, not sim)
- ROS 2 TF2 transforms and coordinate frames for a moving base
- Online sensor fusion (IMU + wheel encoders + GPS → EKF odometry)
- SLAM + Nav2 autonomous navigation
- Edge inference (running models on Pi)

---

## Platform Architecture

```
Cyberwave Cloud (Digital Twin, Dashboard, MQTT Broker)
        ↕ MQTT
Raspberry Pi - Docker Container
    ├── ugv_driver      (hardware drivers)
    ├── ugv_vision      (sensor processing)
    ├── ugv_bringup     (launch)
    └── MQTT Bridge     (ROS 2 ↔ Cyberwave cloud)
        ↕ Serial UART
ESP32 (motors, encoders, IMU, servos, LEDs, OLED)
```

**Two SSH targets (same IP, different ports):**

| Host | User | Port | Purpose |
|------|------|------|---------|
| Raspberry Pi | `ws` | `22` | System admin, Docker management |
| Docker Container | `root` | `23` | ROS 2, MQTT Bridge, Cyberwave config |

---

## Phase 1 - Hardware Bring-Up

**Goal:** SSH into both layers, see ROS 2 topics streaming live.

### SSH Config (add to `~/.ssh/config`)

```
Host ugv-pi
    HostName <UGV_IP>   # shown on OLED (W: line)
    User ws
    Port 22

Host ugv-docker
    HostName <UGV_IP>
    User root
    Port 23
```

### Setup Sequence

```bash
# 0. Connect rover to WiFi (run this from inside the rover via JupyterLab or SSH over AccessPopup)
sudo nmcli dev wifi connect "5G EvoPhilly" ifname wlan0
# The OLED W: line will update with the new IP - use that for all future SSH connections

# 1. Disable the default Waveshare main program (frees serial port + camera)
#    Follow Waveshare prep guide steps 1.1 and 1.2 - then STOP (skip their Docker step)

# 2. SSH into Pi and install Cyberwave
ssh ugv-pi
curl -fsSL https://cyberwave.com/install.sh | bash
sudo cyberwave edge install     # pulls Cyberwave Docker image (~5 min)
cyberwave edge logs             # verify it's running

# 3. SSH into Docker container (ROS 2 environment)
ssh ugv-docker
ros2 topic list                 # see all active topics
ros2 topic echo /imu/data       # live IMU stream
ros2 topic echo /joint_states   # wheel encoder feedback
```

### Key Concepts to Understand

- Why the dual-SSH setup exists (Pi host vs. Docker container)
- The UART bridge: ROS 2 node ↔ serial ↔ ESP32 (what `ugv_driver` does)
- The MQTT bridge: how Cyberwave dashboard commands become ROS 2 messages

---

## Phase 2 - Custom ROS 2 Nodes: Odometry + TF2

**Goal:** Write a Python node that subscribes to IMU + joint states and publishes odometry.

This is the foundational skill for mobile robots - entirely new compared to LeRobot.

**New message types to learn:**
- `nav_msgs/Odometry` - position estimate from wheel encoders
- `tf2_ros.TransformBroadcaster` - broadcasting `odom → base_link`
- `sensor_msgs/Imu`, `sensor_msgs/JointState`
- ROS 2 parameter YAML files

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState, Imu
from nav_msgs.msg import Odometry
import tf2_ros

class OdometryNode(Node):
    def __init__(self):
        super().__init__('odometry_node')
        self.sub_joints = self.create_subscription(
            JointState, '/joint_states', self.joints_cb, 10)
        self.pub_odom = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

    def joints_cb(self, msg):
        # compute pose delta from encoder ticks → publish Odometry + TF
        pass
```

**Deliverables:**
- Working `odom → base_link` TF transform visible in RViz2
- Measure and document drift rate over 5m and 10m traversals - this characterizes dead-reckoning accuracy and motivates the EKF in Phase 3

---

## Phase 3 - Sensor Fusion: EKF (GPS + IMU + Encoders)

**Goal:** Fuse wheel odometry, IMU, and GPS into a single drift-corrected pose estimate using an Extended Kalman Filter.

This addresses the core limitation found in Phase 2 - encoder-only odometry drifts unboundedly over distance. Adding GPS corrections keeps the estimate globally consistent.

### GPS Hardware

The UGV Beast does not have onboard GPS. Two options:

| Option | Cost | Notes |
|--------|------|-------|
| USB GPS puck (u-blox NEO-6M) | ~$20 | Real sensor, plugs into Pi USB, `nmea_navsat_driver` publishes `sensor_msgs/NavSatFix` |
| Simulated GPS publisher | $0 | Python node that adds realistic noise + drift to ground-truth position - label clearly in code |

### EKF Configuration (`ekf.yaml`)

```yaml
ekf_filter_node:
  ros__parameters:
    frequency: 30.0
    odom0: /odom
    odom0_config: [false, false, false,
                   false, false, false,
                   true,  true,  false,
                   false, false, true,
                   false, false, false]
    imu0: /imu/data
    imu0_config: [false, false, false,
                  true,  true,  true,
                  false, false, false,
                  true,  true,  true,
                  true,  false, false]
    odom_frame: odom
    base_link_frame: base_link
    world_frame: odom
```

### Key Concepts

- **Covariance propagation** - how uncertainty grows during prediction and shrinks during update
- **GPS latency** (~1 Hz) vs. IMU rate (~100 Hz) - why IMU integration fills the gaps
- **EKF vs. UKF** - `robot_localization` supports both; EKF linearizes, UKF uses sigma points
- **RTK corrections** - RTCM over NTRIP reduces GPS CEP from ~3m to ~2cm (relevant for precision field robots)

### Packages

```bash
# Install inside Docker container
sudo apt install ros-humble-robot-localization
sudo apt install ros-humble-nmea-navsat-driver   # if using real GPS puck
```

**Deliverable:** `/odometry/filtered` fused pose visible in RViz2, visibly more stable than raw `/odom` when GPS updates arrive. Document the improvement in drift rate vs. Phase 2 baseline.

---

## Phase 4 - Visual SLAM

**Goal:** Build a real-time map of an environment while localizing the rover in it.

### Options (ranked by difficulty)

| Method | Sensor Required | Package |
|--------|----------------|---------|
| 2D LiDAR SLAM | LiDAR (add-on) | `slam_toolbox` |
| Visual-Inertial SLAM | Camera + IMU (built-in) | `rtabmap_ros` |
| Pure Visual Odometry | Camera (built-in) | `ORB-SLAM3` |

**Recommended starting point:** `rtabmap_ros` - uses the onboard camera + IMU, no extra hardware needed.

```bash
# Inside Docker container
ros2 launch rtabmap_ros rtabmap.launch.py \
    rgb_topic:=/camera/image_raw \
    depth_topic:=/camera/depth \
    camera_info_topic:=/camera/camera_info

# Visualize in RViz2
ros2 run rviz2 rviz2
```

**Key concepts:**
- Loop closure detection
- Map serialization (save/load a `.db` map file)
- Localization-only mode on a saved map

**Deliverables:**
- Live occupancy map building in RViz2 while driving
- Saved `.db` map that can be reloaded
- Demonstrate localization-only mode: rover placed back in the same environment, localizes without re-mapping

---

## Phase 5 - Autonomous Navigation (Nav2)

**Goal:** Send the rover a goal pose; have it plan and execute a collision-free path autonomously. Add geofencing to define no-go zones.

### Nav2 Stack Components

| Component | Role |
|-----------|------|
| **Costmaps** | Represent free space + obstacles from sensor data |
| **Global planner** | Finds a path (A*, Dijkstra, etc.) |
| **Local planner (DWB)** | Executes path, avoids dynamic obstacles |
| **AMCL** | Particle filter localization on a saved map |
| **Behavior trees** | Orchestrate recovery behaviors |

```bash
# Launch Nav2 with a saved map from Phase 4
ros2 launch nav2_bringup navigation_launch.py \
    map:=/path/to/saved_map.yaml \
    use_sim_time:=false

# Send a goal programmatically
ros2 run nav2_simple_commander navigate_to_pose
```

### Geofencing (Keepout Zones)

Define exclusion zones (e.g., worker safety areas, hazardous regions) that the rover will never enter:

```python
from nav2_simple_commander.robot_navigator import BasicNavigator

navigator = BasicNavigator()
navigator.loadKeepoutMask('/path/to/keepout_mask.yaml')
```

**Deliverables:**
- Rover navigates autonomously from point A to B, replanning around a dynamically placed obstacle
- Keepout zone demo: defined no-go area in the costmap, rover routes around it

---

## Phase 6 - Construction Inspection Rover Capstone

**Goal:** Deploy a complete autonomous inspection system - the rover patrols a pre-mapped route, captures images at defined waypoints, runs hazard detection, and logs anomalies with position tags to the Cyberwave dashboard.

### Sub-Steps

**6a - Multi-Waypoint Patrol Route**

Use `nav2_simple_commander` to execute a programmatic patrol:

```python
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped

navigator = BasicNavigator()
waypoints = [make_pose(x1, y1), make_pose(x2, y2), make_pose(x3, y3)]
navigator.followWaypoints(waypoints)
```

Connect patrol status to the Cyberwave digital twin via the MQTT bridge so progress streams to the dashboard in real time.

**6b - Image Capture at Waypoints**

On arrival at each waypoint, publish to `/inspection/trigger`. A `ugv_vision` node subscribes, captures a frame from `/camera/image_raw`, and forwards it for analysis.

**6c - Hazard Detection Pipeline**

Two-stage detection:
1. **YOLOv8 (edge, on Pi)** - fast first-pass filter at ~5–10 FPS

```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
results = model(frame)
```

2. **VLM (flagged frames only)** - offload to Cyberwave cloud workflow or local `qwen3:32b`:

```
Prompt: "Does this image show a construction site hazard?
         List any safety concerns observed."
```

**6d - Anomaly Logging with Position Tags**

Tag each detection with the rover's current `/odometry/filtered` pose from the EKF:

```python
anomaly = {
    "timestamp": now.isoformat(),
    "waypoint_id": waypoint_idx,
    "pose_x": odom.pose.pose.position.x,
    "pose_y": odom.pose.pose.position.y,
    "label": detection_label,
    "confidence": confidence,
    "image_url": image_url
}
```

Stream anomaly log entries to the Cyberwave dashboard - anomaly markers appear on the digital twin map.

**6e - Cyberwave Workflow Automation**

Build a Cyberwave visual workflow:

```
Schedule trigger
    → Move to Waypoint
    → Capture Image
    → Analyze Image (VLM)
    → Branch:
        Pass → Move to Next Waypoint
        Fail → Send Alert (email / MQTT publish)
```

### Deliverables

- **Demo video:** rover executes full patrol route, stops at each waypoint, detects and logs a placed hazard (orange cone, safety vest), alert triggers on detection
- **Cyberwave dashboard screenshot:** live telemetry, anomaly markers on the map, detection log
- **README:** system architecture diagram mapping each component to the broader autonomous inspection stack

---

## Weekly Schedule

| Week | Phase | Deliverable |
|------|-------|-------------|
| 1 | 1 + 2 | Live topics + TF tree in RViz2; drift rate documented |
| 2 | 3 (EKF) | Fused `/odometry/filtered` in RViz2; `ekf.yaml` with covariance rationale |
| 3 | 4 (SLAM) | Live map building; localization-only demo on saved map |
| 4 | 5 (Nav2) + 6a | Autonomous A→B + obstacle replan; keepout demo; patrol script |
| 5 | 6b + 6c | Edge YOLOv8 running live; VLM hazard prompts working |
| 6 | 6d + 6e | Full inspection demo video; Cyberwave anomaly map |

---

## Useful Commands Reference

```bash
# ROS 2 introspection
ros2 topic list
ros2 topic echo <topic>
ros2 topic hz <topic>          # check publish rate
ros2 node list
ros2 node info <node>
ros2 run tf2_tools view_frames  # visualize TF tree

# Cyberwave CLI
cyberwave edge logs
cyberwave edge status
cyberwave edge restart

# RViz2 (run on Mac with ROS 2 installed, or via Docker with display forwarding)
ros2 run rviz2 rviz2
```

---

## Packages Reference

| Package | Phase | Purpose |
|---------|-------|---------|
| `robot_localization` | 3 | EKF/UKF sensor fusion |
| `nmea_navsat_driver` | 3 | GPS NMEA → NavSatFix |
| `rtabmap_ros` | 4 | Visual-inertial SLAM |
| `nav2_bringup` | 5 | Full Nav2 stack launch |
| `nav2_simple_commander` | 5, 6 | Python waypoint API |
| `nav2_costmap_2d` | 5 | Keepout / geofencing layers |
| `ultralytics` YOLOv8 | 6 | Edge object detection |
| Cyberwave Python SDK | 6 | MQTT bridge, VLM, workflows |

---

## Resources

- [Cyberwave UGV Docs](https://docs.cyberwave.com/hardware/ugv/index)
- [Cyberwave Get Started](https://docs.cyberwave.com/hardware/ugv/get-started)
- [Cyberwave Idea Cookbook](https://docs.cyberwave.com/get-started/idea-cookbook)
- [robot_localization](https://docs.ros.org/en/humble/p/robot_localization/)
- [Nav2 Documentation](https://docs.nav2.org/)
- [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [rtabmap_ros](https://github.com/introlab/rtabmap_ros)
- [Waveshare UGV Beast Wiki](https://www.waveshare.com/wiki/UGV_Beast_PI_ROS2)
