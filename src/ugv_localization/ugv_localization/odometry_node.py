"""
Differential drive odometry node for UGV Beast.

Subscribes to /joint_states (wheel encoders) and optionally /imu/data,
computes dead-reckoning pose, publishes /odom and broadcasts odom -> base_link TF.
"""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState, Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped, Quaternion
import tf2_ros


def yaw_to_quaternion(yaw: float) -> Quaternion:
    """Convert a yaw angle (radians) to a geometry_msgs Quaternion."""
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


def quaternion_to_yaw(q: Quaternion) -> float:
    """Extract yaw from a geometry_msgs Quaternion (assuming planar motion)."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class OdometryNode(Node):
    def __init__(self):
        super().__init__('odometry_node')

        # --- Parameters ---
        self.declare_parameter('wheel_radius', 0.05)        # TODO: measure on hardware
        self.declare_parameter('wheel_base', 0.3)            # TODO: measure on hardware
        self.declare_parameter('encoder_ticks_per_rev', 1440) # TODO: check ESP32 datasheet
        self.declare_parameter('left_joint_name', 'left_wheel_joint')   # TODO: match ugv_driver
        self.declare_parameter('right_joint_name', 'right_wheel_joint') # TODO: match ugv_driver
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_link_frame', 'base_link')
        self.declare_parameter('use_imu', False)
        self.declare_parameter('publish_tf', True)

        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_base = self.get_parameter('wheel_base').value
        self.ticks_per_rev = self.get_parameter('encoder_ticks_per_rev').value
        self.left_joint = self.get_parameter('left_joint_name').value
        self.right_joint = self.get_parameter('right_joint_name').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_link_frame = self.get_parameter('base_link_frame').value
        self.use_imu = self.get_parameter('use_imu').value
        self.publish_tf = self.get_parameter('publish_tf').value

        # Meters per encoder tick
        self.meters_per_tick = (2.0 * math.pi * self.wheel_radius) / self.ticks_per_rev

        # --- State ---
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.prev_left_pos = None
        self.prev_right_pos = None
        self.prev_time = None
        self.imu_yaw = None  # latest IMU yaw, if available

        # --- Publishers ---
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # --- TF Broadcaster ---
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # --- Subscriptions ---
        self.create_subscription(JointState, '/joint_states', self._joint_states_cb, 10)

        if self.use_imu:
            self.create_subscription(Imu, '/imu/data', self._imu_cb, 10)
            self.get_logger().info('IMU fusion enabled — subscribing to /imu/data')

        self.get_logger().info(
            f'OdometryNode started — wheel_radius={self.wheel_radius}, '
            f'wheel_base={self.wheel_base}, ticks_per_rev={self.ticks_per_rev}'
        )

    def _imu_cb(self, msg: Imu):
        """Cache the latest IMU yaw for optional heading correction."""
        self.imu_yaw = quaternion_to_yaw(msg.orientation)

    def _joint_states_cb(self, msg: JointState):
        """Process encoder ticks, compute odometry, publish."""
        # Find left and right joint indices
        try:
            left_idx = msg.name.index(self.left_joint)
            right_idx = msg.name.index(self.right_joint)
        except ValueError:
            self.get_logger().warn(
                f'Expected joints [{self.left_joint}, {self.right_joint}] '
                f'not found in JointState names: {msg.name}',
                throttle_duration_sec=5.0,
            )
            return

        left_pos = msg.position[left_idx]
        right_pos = msg.position[right_idx]
        now = self.get_clock().now()

        # First message: initialize state, don't publish yet
        if self.prev_left_pos is None:
            self.prev_left_pos = left_pos
            self.prev_right_pos = right_pos
            self.prev_time = now
            self.get_logger().info('Encoder state initialized — waiting for next message')
            return

        # Compute time delta
        dt = (now - self.prev_time).nanoseconds * 1e-9
        if dt <= 0.0:
            return

        # Compute distance traveled by each wheel
        delta_left = (left_pos - self.prev_left_pos) * self.meters_per_tick
        delta_right = (right_pos - self.prev_right_pos) * self.meters_per_tick

        # Differential drive kinematics
        delta_s = (delta_right + delta_left) / 2.0       # linear displacement
        delta_theta = (delta_right - delta_left) / self.wheel_base  # angular displacement

        # Integrate pose
        self.theta += delta_theta
        self.x += delta_s * math.cos(self.theta)
        self.y += delta_s * math.sin(self.theta)

        # If IMU is available, override heading with IMU yaw
        if self.use_imu and self.imu_yaw is not None:
            self.theta = self.imu_yaw

        # Compute velocities
        v_linear = delta_s / dt
        v_angular = delta_theta / dt

        # Build Odometry message
        odom_msg = Odometry()
        odom_msg.header.stamp = now.to_msg()
        odom_msg.header.frame_id = self.odom_frame
        odom_msg.child_frame_id = self.base_link_frame

        # Pose
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0
        odom_msg.pose.pose.orientation = yaw_to_quaternion(self.theta)

        # Pose covariance (6x6, row-major) — diagonal only
        # [x, y, z, roll, pitch, yaw]
        odom_msg.pose.covariance[0] = 0.01   # x
        odom_msg.pose.covariance[7] = 0.01   # y
        odom_msg.pose.covariance[14] = 1e6   # z (not measured, very uncertain)
        odom_msg.pose.covariance[21] = 1e6   # roll
        odom_msg.pose.covariance[28] = 1e6   # pitch
        odom_msg.pose.covariance[35] = 0.03  # yaw

        # Twist (in child_frame_id = base_link)
        odom_msg.twist.twist.linear.x = v_linear
        odom_msg.twist.twist.angular.z = v_angular

        # Twist covariance
        odom_msg.twist.covariance[0] = 0.01   # vx
        odom_msg.twist.covariance[7] = 0.01   # vy
        odom_msg.twist.covariance[14] = 1e6   # vz
        odom_msg.twist.covariance[21] = 1e6   # vroll
        odom_msg.twist.covariance[28] = 1e6   # vpitch
        odom_msg.twist.covariance[35] = 0.03  # vyaw

        self.odom_pub.publish(odom_msg)

        # Broadcast TF: odom -> base_link
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = now.to_msg()
            t.header.frame_id = self.odom_frame
            t.child_frame_id = self.base_link_frame
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation = yaw_to_quaternion(self.theta)
            self.tf_broadcaster.sendTransform(t)

        # Update state
        self.prev_left_pos = left_pos
        self.prev_right_pos = right_pos
        self.prev_time = now


def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
