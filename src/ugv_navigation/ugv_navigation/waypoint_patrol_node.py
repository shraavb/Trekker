"""
Waypoint patrol node.

Executes a sequence of waypoints using Nav2's BasicNavigator.
Publishes patrol status on /patrol/status as JSON and triggers
inspection at each waypoint via /inspection/trigger.
"""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped

# nav2_simple_commander may not be installed in dev environments
try:
    from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
    HAS_NAV2 = True
except ImportError:
    HAS_NAV2 = False


class WaypointPatrolNode(Node):
    def __init__(self):
        super().__init__('waypoint_patrol_node')

        # Waypoints as flat list: [x1, y1, yaw1, x2, y2, yaw2, ...]
        # TODO: load from a YAML config or parameter server
        self.declare_parameter('waypoints', [0.0, 0.0, 0.0])
        self.declare_parameter('loop', False)

        raw_waypoints = self.get_parameter('waypoints').value
        self.loop = self.get_parameter('loop').value

        # Parse flat list into list of (x, y, yaw) tuples
        self.waypoints = []
        for i in range(0, len(raw_waypoints) - 2, 3):
            self.waypoints.append((raw_waypoints[i], raw_waypoints[i+1], raw_waypoints[i+2]))

        self.status_pub = self.create_publisher(String, '/patrol/status', 10)
        self.trigger_pub = self.create_publisher(String, '/inspection/trigger', 10)

        self.get_logger().info(f'WaypointPatrolNode initialized with {len(self.waypoints)} waypoints')

        if not HAS_NAV2:
            self.get_logger().warn(
                'nav2_simple_commander not installed — patrol will not execute. '
                'Install Nav2 to enable autonomous navigation.'
            )

    def _make_pose(self, x: float, y: float, yaw: float) -> PoseStamped:
        """Create a PoseStamped from x, y, yaw."""
        import math
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    def _publish_status(self, waypoint_idx: int, state: str):
        """Publish patrol status as JSON."""
        status = {
            'waypoint_index': waypoint_idx,
            'total_waypoints': len(self.waypoints),
            'state': state,
        }
        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)

    def run_patrol(self):
        """Execute the waypoint patrol sequence."""
        if not HAS_NAV2:
            self.get_logger().error('Cannot run patrol without nav2_simple_commander')
            return

        navigator = BasicNavigator()
        navigator.waitUntilNav2Active()

        self.get_logger().info('Nav2 active — starting patrol')

        while rclpy.ok():
            for idx, (x, y, yaw) in enumerate(self.waypoints):
                self._publish_status(idx, 'navigating')
                self.get_logger().info(f'Navigating to waypoint {idx}: ({x}, {y})')

                goal_pose = self._make_pose(x, y, yaw)
                navigator.goToPose(goal_pose)

                # Wait for navigation to complete
                while not navigator.isTaskComplete():
                    rclpy.spin_once(self, timeout_sec=0.5)

                result = navigator.getResult()
                if result == TaskResult.SUCCEEDED:
                    self._publish_status(idx, 'arrived')
                    self.get_logger().info(f'Arrived at waypoint {idx}')

                    # Trigger inspection
                    trigger_msg = String()
                    trigger_msg.data = str(idx)
                    self.trigger_pub.publish(trigger_msg)
                    self._publish_status(idx, 'capturing')

                    # TODO: wait for inspection pipeline to complete before moving on

                elif result == TaskResult.CANCELED:
                    self.get_logger().warn(f'Navigation to waypoint {idx} was canceled')
                    self._publish_status(idx, 'error')
                else:
                    self.get_logger().error(f'Navigation to waypoint {idx} failed')
                    self._publish_status(idx, 'error')

            self._publish_status(len(self.waypoints) - 1, 'complete')

            if not self.loop:
                break

            self.get_logger().info('Patrol complete — looping')


def main(args=None):
    rclpy.init(args=args)
    node = WaypointPatrolNode()
    try:
        node.run_patrol()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
