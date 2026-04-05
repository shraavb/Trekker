"""
Stub joint state publisher for UGV Beast wheel encoders.
Publishes /joint_states at ~50 Hz with zeroed positions until real encoder driver is available.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class JointStateNode(Node):
    def __init__(self):
        super().__init__('joint_state_node')
        self.pub = self.create_publisher(JointState, '/joint_states', 10)
        self.timer = self.create_timer(0.02, self.publish)  # 50 Hz
        self.left_pos = 0.0
        self.right_pos = 0.0
        self.get_logger().info('JointStateNode ready — publishing /joint_states at 50 Hz')

    def publish(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ['left_wheel_joint', 'right_wheel_joint']
        msg.position = [self.left_pos, self.right_pos]
        msg.velocity = [0.0, 0.0]
        msg.effort = [0.0, 0.0]
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = JointStateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
