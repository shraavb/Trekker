# Trekker 🏔️

Autonomous construction site inspection rover built on [Cyberwave](https://cyberwave.com).

Trekker patrols a pre-mapped environment, detects hazards using a YOLOv8 + VLM pipeline, and streams position-tagged anomaly logs to a live supervisory dashboard — all running on a UGV Beast rover.

---

## System Overview

```
Cyberwave Cloud (Digital Twin, Dashboard, MQTT Broker)
        ↕ MQTT
Raspberry Pi - Docker Container
    ├── ugv_driver      (hardware drivers)
    ├── ugv_vision      (sensor processing + YOLOv8)
    ├── ugv_bringup     (launch)
    └── MQTT Bridge     (ROS 2 ↔ Cyberwave cloud)
        ↕ Serial UART
ESP32 (motors, encoders, IMU, servos, LEDs, OLED)
```

## Stack

| Layer | Technology |
|-------|-----------|
| Platform | [Cyberwave](https://cyberwave.com) |
| Hardware | Waveshare UGV Beast (Raspberry Pi 4 + ESP32) |
| Middleware | ROS 2 (Humble) |
| Localization | EKF via `robot_localization` (GPS + IMU + wheel encoders) |
| Mapping | Visual SLAM via `rtabmap_ros` |
| Navigation | Nav2 with geofenced keepout zones |
| Perception | YOLOv8 (edge) + VLM hazard classification (cloud) |
| Dashboard | Cyberwave digital twin + anomaly map |

## Phases

1. **Hardware Bring-Up** - SSH setup, Cyberwave install, verify ROS 2 topics live
2. **Odometry + TF2** - Wheel encoder dead-reckoning, `odom -> base_link` TF
3. **Sensor Fusion (EKF)** - GPS + IMU + encoder fusion via `robot_localization`
4. **Visual SLAM** - Real-time map building + localization-only mode
5. **Nav2 Navigation** - Autonomous waypoint navigation + geofenced exclusion zones
6. **Inspection Capstone** - Autonomous patrol, hazard detection, anomaly logging to Cyberwave dashboard

## Hardware

- Waveshare UGV Beast (tracked rover, Raspberry Pi 4B, ESP32, onboard camera, IMU)
- Optional: u-blox NEO-6M USB GPS puck (~$20) for Phase 3

## Resources

- [Cyberwave Docs](https://docs.cyberwave.com)
- [Waveshare UGV Beast Wiki](https://www.waveshare.com/wiki/UGV_Beast_PI_ROS2)
- [Nav2 Docs](https://docs.nav2.org/)
- [robot_localization](https://docs.ros.org/en/humble/p/robot_localization/)
