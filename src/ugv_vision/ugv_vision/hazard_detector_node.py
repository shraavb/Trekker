"""
Hazard detection node.

Subscribes to /inspection/captured_image and /odometry/filtered.
Runs detection (YOLOv8 stub), publishes position-tagged anomaly
reports to /inspection/anomalies as JSON.
"""

import json
from datetime import datetime, timezone

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from std_msgs.msg import String

# YOLOv8 is optional — stub for environments without ultralytics
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

# cv_bridge is optional
try:
    from cv_bridge import CvBridge
    HAS_CV_BRIDGE = True
except ImportError:
    HAS_CV_BRIDGE = False


class HazardDetectorNode(Node):
    def __init__(self):
        super().__init__('hazard_detector_node')

        self.declare_parameter('model_path', 'yolov8n.pt')  # TODO: path to trained model
        self.declare_parameter('confidence_threshold', 0.5)

        self.model_path = self.get_parameter('model_path').value
        self.conf_threshold = self.get_parameter('confidence_threshold').value

        self.current_pose = None
        self.bridge = CvBridge() if HAS_CV_BRIDGE else None
        self.model = None

        if HAS_YOLO:
            try:
                self.model = YOLO(self.model_path)
                self.get_logger().info(f'YOLOv8 model loaded: {self.model_path}')
            except Exception as e:
                self.get_logger().error(f'Failed to load YOLO model: {e}')
        else:
            self.get_logger().warn(
                'ultralytics not installed — hazard detection will use stub. '
                'Install with: pip install ultralytics'
            )

        self.create_subscription(Image, '/inspection/captured_image', self._image_cb, 10)
        self.create_subscription(Odometry, '/odometry/filtered', self._odom_cb, 10)
        self.anomaly_pub = self.create_publisher(String, '/inspection/anomalies', 10)

        self.get_logger().info('HazardDetectorNode ready')

    def _odom_cb(self, msg: Odometry):
        """Cache current EKF-fused pose for position tagging."""
        self.current_pose = msg.pose.pose

    def _image_cb(self, msg: Image):
        """Run detection on captured image, publish anomaly if found."""
        detections = self._detect(msg)

        for det in detections:
            anomaly = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'label': det['label'],
                'confidence': det['confidence'],
                'pose_x': self.current_pose.position.x if self.current_pose else 0.0,
                'pose_y': self.current_pose.position.y if self.current_pose else 0.0,
                'bbox': det.get('bbox', []),
            }

            anomaly_msg = String()
            anomaly_msg.data = json.dumps(anomaly)
            self.anomaly_pub.publish(anomaly_msg)
            self.get_logger().info(f'Anomaly detected: {det["label"]} ({det["confidence"]:.2f})')

    def _detect(self, image_msg: Image) -> list:
        """
        Run hazard detection on an image.

        Returns a list of dicts: [{'label': str, 'confidence': float, 'bbox': [x1,y1,x2,y2]}]
        """
        if self.model and self.bridge:
            cv_image = self.bridge.imgmsg_to_cv2(image_msg, 'bgr8')
            results = self.model(cv_image, conf=self.conf_threshold)

            detections = []
            for r in results:
                for box in r.boxes:
                    detections.append({
                        'label': r.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist(),
                    })
            return detections

        # Stub: no detections when model is unavailable
        self.get_logger().debug('No YOLO model — returning empty detections')
        return []


def main(args=None):
    rclpy.init(args=args)
    node = HazardDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
