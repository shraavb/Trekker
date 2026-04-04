"""
Image capture node.

Subscribes to /camera/image_raw and buffers the latest frame.
On receiving a capture request from /inspection/capture_request,
publishes the current frame to /inspection/captured_image.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

# cv_bridge is optional — guard import for environments without it
try:
    from cv_bridge import CvBridge
    HAS_CV_BRIDGE = True
except ImportError:
    HAS_CV_BRIDGE = False


class ImageCaptureNode(Node):
    def __init__(self):
        super().__init__('image_capture_node')

        self.latest_image = None
        self.bridge = CvBridge() if HAS_CV_BRIDGE else None

        self.create_subscription(Image, '/camera/image_raw', self._image_cb, 10)
        self.create_subscription(String, '/inspection/capture_request', self._capture_cb, 10)
        self.image_pub = self.create_publisher(Image, '/inspection/captured_image', 10)

        if not HAS_CV_BRIDGE:
            self.get_logger().warn('cv_bridge not available — image conversion will be limited')

        self.get_logger().info('ImageCaptureNode ready — buffering /camera/image_raw')

    def _image_cb(self, msg: Image):
        """Buffer the latest camera frame."""
        self.latest_image = msg

    def _capture_cb(self, msg: String):
        """On capture request, publish the buffered frame."""
        if self.latest_image is None:
            self.get_logger().warn('Capture requested but no image buffered yet')
            return

        self.get_logger().info(f'Capturing image for request: {msg.data}')
        self.image_pub.publish(self.latest_image)

        # TODO: optionally save to disk
        # if self.bridge:
        #     cv_image = self.bridge.imgmsg_to_cv2(self.latest_image, 'bgr8')
        #     cv2.imwrite(f'/tmp/inspection_{msg.data}.jpg', cv_image)


def main(args=None):
    rclpy.init(args=args)
    node = ImageCaptureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
