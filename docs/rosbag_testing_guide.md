# Rosbag Testing Guide

Offline development workflow for Trekker — record sensor data on the rover, replay on your dev machine.

## 1. Record on the Rover

SSH into the Docker container and run the recording script:

```bash
ssh ugv-docker
cd /path/to/Trekker
bash scripts/rosbag_record.sh
# Drive the rover around for 1-5 minutes, then Ctrl+C
```

This records: `/joint_states`, `/imu/data`, `/camera/image_raw`, `/camera/camera_info`, `/odom`, `/tf`, `/tf_static`

## 2. Transfer to Dev Machine

```bash
scp -P 23 -r root@<UGV_IP>:/root/trekker_<timestamp> ~/bags/
```

## 3. Play Back with Simulation Clock

In terminal 1 — play the bag:
```bash
bash scripts/rosbag_playback.sh ~/bags/trekker_20250401_143000
```

In terminal 2 — launch nodes with sim time:
```bash
ros2 launch ugv_localization localization.launch.py use_sim_time:=true
```

The `--clock` flag in the playback script publishes `/clock`, and `use_sim_time:=true` makes nodes use that clock instead of wall time.

## 4. Verify Odometry Output

```bash
# Check /odom is publishing
ros2 topic echo /odom --once

# Check TF tree
ros2 run tf2_tools view_frames

# Check publish rate
ros2 topic hz /odom
```

## 5. Visualize in RViz2

```bash
ros2 run rviz2 rviz2
```

Add displays:
- **TF** — verify `odom -> base_link` transform
- **Odometry** — topic: `/odom`, shows position + heading arrows
- **Image** — topic: `/camera/image_raw` (if recorded)

## 6. Test with EKF

```bash
ros2 launch ugv_localization localization.launch.py \
    use_sim_time:=true \
    use_ekf:=true \
    use_imu:=true
```

Compare `/odom` (raw) vs `/odometry/filtered` (EKF-fused) in RViz2.

## Config File Locations

| Config | Path |
|--------|------|
| EKF parameters | `src/ugv_localization/config/ekf.yaml` |
| Nav2 parameters | `src/ugv_navigation/config/nav2_params.yaml` |

## Tips

- Always use `use_sim_time:=true` when replaying bags
- Record at least 1-2 minutes of data with varied motion (straight, turns, stops)
- If `/joint_states` joint names don't match the odometry node's parameters, update `left_joint_name` and `right_joint_name`
- Check `ros2 topic echo /joint_states --once` to see the actual joint names from hardware
