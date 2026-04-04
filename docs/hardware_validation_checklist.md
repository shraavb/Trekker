# Hardware Validation Checklist

Run through this checklist when first connecting to the UGV Beast to verify all systems are operational before running Trekker nodes.

## Prerequisites

- [ ] Rover powered on and connected to WiFi (check OLED W: line for IP)
- [ ] SSH access to Pi host: `ssh ugv-pi`
- [ ] SSH access to Docker container: `ssh ugv-docker`
- [ ] Cyberwave edge installed: `cyberwave edge status`

## 1. Topic Verification

Run inside Docker container (`ssh ugv-docker`):

```bash
ros2 topic list
```

### Expected Topics

| Topic | Message Type | Expected Rate | Notes |
|-------|-------------|---------------|-------|
| `/joint_states` | `sensor_msgs/JointState` | ~50 Hz | Wheel encoder positions |
| `/imu/data` | `sensor_msgs/Imu` | ~100 Hz | Orientation + angular velocity + accel |
| `/camera/image_raw` | `sensor_msgs/Image` | ~30 Hz | RGB camera stream |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | ~30 Hz | Camera intrinsics |
| `/tf` | `tf2_msgs/TFMessage` | varies | Transform tree |
| `/tf_static` | `tf2_msgs/TFMessage` | latched | Static transforms |

Check publish rates:
```bash
ros2 topic hz /joint_states
ros2 topic hz /imu/data
ros2 topic hz /camera/image_raw
```

## 2. JointState Inspection

```bash
ros2 topic echo /joint_states --once
```

Verify:
- [ ] `name` field contains joint names (record these — needed for odometry node params)
- [ ] `position` field is changing when wheels move
- [ ] Values are in expected units (ticks or radians — check ugv_driver docs)

**Record the joint names here:** `_________________`, `_________________`

Update `left_joint_name` and `right_joint_name` parameters in the odometry node accordingly.

## 3. IMU Inspection

```bash
ros2 topic echo /imu/data --once
```

Verify:
- [ ] `orientation` quaternion is non-zero (w should be ~1.0 when level)
- [ ] `angular_velocity` changes when rover rotates
- [ ] `linear_acceleration` z-component is ~9.81 when stationary (gravity)

## 4. Camera Inspection

```bash
# Check image dimensions and encoding
ros2 topic echo /camera/camera_info --once

# View image (if display available)
ros2 run rqt_image_view rqt_image_view
```

Verify:
- [ ] Image resolution matches expected (e.g., 640x480)
- [ ] Image encoding is `rgb8` or `bgr8`
- [ ] Frame rate is stable

## 5. TF Tree

```bash
ros2 run tf2_tools view_frames
```

Verify:
- [ ] `base_link` frame exists
- [ ] Camera frame is connected to `base_link`
- [ ] No broken links in the tree

## 6. Node List

```bash
ros2 node list
```

Record active nodes from `ugv_driver` — these are the hardware interface nodes that Trekker depends on.

## 7. Physical Measurements

Measure and record (needed for odometry node parameters):

| Parameter | Value | Unit |
|-----------|-------|------|
| Wheel radius | _____ | meters |
| Wheel base (track width) | _____ | meters |
| Encoder ticks per revolution | _____ | ticks |

## 8. Record a Test Bag

```bash
bash scripts/rosbag_record.sh
# Drive forward ~2m, turn 90°, drive ~2m, stop
# Ctrl+C to stop recording
```

- [ ] Bag recorded successfully
- [ ] Bag size is reasonable (~100MB/min with camera)
- [ ] Transfer bag to dev machine for offline testing

## 9. Automated Validation

Run the automated script:
```bash
bash scripts/validate_hardware.sh
```

- [ ] All checks pass

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No topics visible | Check `ugv_driver` is running: `ros2 node list` |
| `/joint_states` not publishing | Check serial UART connection to ESP32 |
| Camera topic missing | Camera may be claimed by Waveshare default program — ensure it's disabled (Phase 1 setup) |
| IMU data all zeros | ESP32 may need reboot: power cycle the rover |
| Wrong joint names | Run `ros2 topic echo /joint_states --once` and update params |
