#!/bin/bash
# =============================================================================
# Play back a recorded rosbag with simulation clock.
#
# Usage:
#   bash scripts/rosbag_playback.sh <path_to_bag>
#
# Then launch nodes with use_sim_time:=true:
#   ros2 launch ugv_localization localization.launch.py use_sim_time:=true
# =============================================================================

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <path_to_rosbag>"
    echo "Example: $0 trekker_20250401_143000"
    exit 1
fi

BAG_PATH="$1"

if [ ! -d "$BAG_PATH" ]; then
    echo "Error: bag directory not found: $BAG_PATH"
    exit 1
fi

echo "Playing back: ${BAG_PATH}"
echo "Publishing /clock for use_sim_time"
echo "Press Ctrl+C to stop"
echo "---"

ros2 bag play "$BAG_PATH" --clock
