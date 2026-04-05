"""
Stub camera publisher for UGV Beast.
Publishes /camera/image_raw and /camera/camera_info at ~30 Hz until real camera driver is available.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo


class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        self.timer = self.create_timer(1.0 / 30.0, self.publish)  # 30 Hz
        self.get_logger().info('CameraNode ready — publishing /camera/image_raw and /camera/camera_info at 30 Hz')

    def publish(self):
        now = self.get_clock().now().to_msg()

        img = Image()
        img.header.stamp = now
        img.header.frame_id = 'camera_link'
        img.height = 480
        img.width = 640
        img.encoding = 'rgb8'
        img.step = 640 * 3
        img.data = [0] * (640 * 480 * 3)
        self.image_pub.publish(img)

        info = CameraInfo()
        info.header.stamp = now
        info.header.frame_id = 'camera_link'
        info.height = 480
        info.width = 640
        info.distortion_model = 'plumb_bob'
        self.info_pub.publish(info)


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
