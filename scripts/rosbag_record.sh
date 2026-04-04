#!/bin/bash
# =============================================================================
# Record key topics for offline development and testing.
#
# Run this on the rover (inside Docker container via ssh ugv-docker):
#   bash scripts/rosbag_record.sh
#
# Transfer the resulting bag to your dev machine:
#   scp -P 23 -r root@<UGV_IP>:/root/trekker_<timestamp> .
# =============================================================================

set -euo pipefail

TOPICS=(
    /joint_states
    /imu/data
    /camera/image_raw
    /camera/camera_info
    /odom
    /odometry/filtered
    /tf
    /tf_static
)

BAGNAME="trekker_$(date +%Y%m%d_%H%M%S)"

echo "Recording topics to: ${BAGNAME}"
echo "Topics: ${TOPICS[*]}"
echo "Press Ctrl+C to stop recording"
echo "---"

ros2 bag record -o "$BAGNAME" "${TOPICS[@]}"
