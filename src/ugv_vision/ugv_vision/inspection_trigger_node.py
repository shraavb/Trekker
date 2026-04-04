"""
Inspection trigger node.

Subscribes to /inspection/trigger and publishes capture requests
to /inspection/capture_request. Acts as the orchestration entry point
for the inspection pipeline.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class InspectionTriggerNode(Node):
    def __init__(self):
        super().__init__('inspection_trigger_node')

        self.create_subscription(String, '/inspection/trigger', self._trigger_cb, 10)
        self.capture_pub = self.create_publisher(String, '/inspection/capture_request', 10)

        self.get_logger().info('InspectionTriggerNode ready — waiting for triggers on /inspection/trigger')

    def _trigger_cb(self, msg: String):
        """Forward trigger as a capture request with waypoint context."""
        self.get_logger().info(f'Inspection triggered: {msg.data}')

        request = String()
        request.data = msg.data  # pass through waypoint_id or trigger payload
        self.capture_pub.publish(request)


def main(args=None):
    rclpy.init(args=args)
    node = InspectionTriggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
