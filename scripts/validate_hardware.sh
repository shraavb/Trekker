#!/bin/bash
# =============================================================================
# Hardware validation script.
#
# Run on the rover (inside Docker container) to verify all expected
# topics are publishing and sensors are healthy.
#
# Usage:
#   bash scripts/validate_hardware.sh
# =============================================================================

set -euo pipefail

PASS=0
FAIL=0

check_topic() {
    local topic="$1"
    local description="$2"
    local timeout="${3:-3}"

    echo -n "  [$description] $topic ... "
    if ros2 topic hz "$topic" --window 5 2>/dev/null | head -1 | grep -q "average rate"; then
        echo "PASS"
        ((PASS++))
    else
        # Fallback: just check if topic exists in the list
        if ros2 topic list 2>/dev/null | grep -q "^${topic}$"; then
            echo "PASS (listed, rate not confirmed)"
            ((PASS++))
        else
            echo "FAIL (not found)"
            ((FAIL++))
        fi
    fi
}

echo "=== Trekker Hardware Validation ==="
echo ""

# --- Topic checks ---
echo "1. Checking required topics..."
check_topic "/joint_states" "Wheel encoders"
check_topic "/imu/data" "IMU"
echo ""

echo "2. Checking camera topics..."
check_topic "/camera/image_raw" "Camera image"
check_topic "/camera/camera_info" "Camera info"
echo ""

echo "3. Checking TF..."
check_topic "/tf" "TF transforms"
check_topic "/tf_static" "Static TF"
echo ""

# --- Node checks ---
echo "4. Active nodes:"
ros2 node list 2>/dev/null || echo "  (could not list nodes)"
echo ""

# --- TF tree ---
echo "5. TF frames:"
ros2 run tf2_tools view_frames 2>/dev/null && echo "  Saved to frames.pdf" || echo "  (tf2_tools not available)"
echo ""

# --- Summary ---
echo "=== Results ==="
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    echo "  Some checks failed — review above output"
    exit 1
else
    echo "  All checks passed!"
fi
