"""
MQTT bridge node.

Bridges ROS 2 topics to/from MQTT for Cyberwave dashboard integration.
Subscribes to /patrol/status and /inspection/anomalies, forwards to MQTT.
Subscribes to MQTT commands and republishes as ROS 2 messages.
"""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry

# paho-mqtt is optional — guard for environments without it
try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False


class MQTTBridgeNode(Node):
    def __init__(self):
        super().__init__('mqtt_bridge_node')

        # --- MQTT Parameters ---
        self.declare_parameter('mqtt_host', 'localhost')       # TODO: set to Cyberwave broker
        self.declare_parameter('mqtt_port', 1883)
        self.declare_parameter('mqtt_username', '')             # TODO: Cyberwave credentials
        self.declare_parameter('mqtt_password', '')             # TODO: Cyberwave credentials
        self.declare_parameter('mqtt_topic_prefix', 'trekker')

        self.mqtt_host = self.get_parameter('mqtt_host').value
        self.mqtt_port = self.get_parameter('mqtt_port').value
        self.mqtt_username = self.get_parameter('mqtt_username').value
        self.mqtt_password = self.get_parameter('mqtt_password').value
        self.topic_prefix = self.get_parameter('mqtt_topic_prefix').value

        # --- MQTT Client ---
        self.mqtt_client = None
        if HAS_MQTT:
            self.mqtt_client = mqtt.Client()
            if self.mqtt_username:
                self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message

            try:
                self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
                self.mqtt_client.loop_start()
                self.get_logger().info(f'MQTT connected to {self.mqtt_host}:{self.mqtt_port}')
            except Exception as e:
                self.get_logger().error(f'MQTT connection failed: {e}')
                self.mqtt_client = None
        else:
            self.get_logger().warn(
                'paho-mqtt not installed — MQTT bridge disabled. '
                'Install with: pip install paho-mqtt'
            )

        # --- ROS Subscriptions (forward to MQTT) ---
        self.create_subscription(String, '/patrol/status', self._patrol_status_cb, 10)
        self.create_subscription(String, '/inspection/anomalies', self._anomaly_cb, 10)
        self.create_subscription(Odometry, '/odometry/filtered', self._odom_cb, 10)

        # --- ROS Publishers (from MQTT commands) ---
        self.command_pub = self.create_publisher(String, '/dashboard/commands', 10)
        self.trigger_pub = self.create_publisher(String, '/inspection/trigger', 10)

        self.get_logger().info('MQTTBridgeNode ready')

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Subscribe to MQTT command topics on connect."""
        self.get_logger().info(f'MQTT connected (rc={rc})')
        client.subscribe(f'{self.topic_prefix}/commands/#')

    def _on_mqtt_message(self, client, userdata, msg):
        """Forward MQTT messages to ROS topics."""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        self.get_logger().info(f'MQTT message: {topic} -> {payload}')

        if topic.endswith('/trigger'):
            ros_msg = String()
            ros_msg.data = payload
            self.trigger_pub.publish(ros_msg)
        else:
            ros_msg = String()
            ros_msg.data = payload
            self.command_pub.publish(ros_msg)

    def _mqtt_publish(self, topic: str, payload: str):
        """Publish to MQTT if connected."""
        if self.mqtt_client:
            self.mqtt_client.publish(f'{self.topic_prefix}/{topic}', payload)

    def _patrol_status_cb(self, msg: String):
        """Forward patrol status to MQTT."""
        self._mqtt_publish('patrol/status', msg.data)

    def _anomaly_cb(self, msg: String):
        """Forward anomaly reports to MQTT."""
        self._mqtt_publish('anomalies', msg.data)
        self.get_logger().info(f'Anomaly forwarded to MQTT: {msg.data[:100]}...')

    def _odom_cb(self, msg: Odometry):
        """Forward pose telemetry to MQTT (throttled)."""
        pose = {
            'x': msg.pose.pose.position.x,
            'y': msg.pose.pose.position.y,
            'z': msg.pose.pose.position.z,
        }
        self._mqtt_publish('telemetry/pose', json.dumps(pose))

    def destroy_node(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MQTTBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
