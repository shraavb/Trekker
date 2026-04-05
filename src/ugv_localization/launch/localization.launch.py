"""Launch file for ugv_localization: odometry node + optional EKF."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('ugv_localization')
    ekf_config = os.path.join(pkg_share, 'config', 'ekf.yaml')

    return LaunchDescription([
        # --- Arguments ---
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='Use simulation clock from rosbag'),
        DeclareLaunchArgument('use_ekf', default_value='false',
                              description='Launch EKF from robot_localization'),
        DeclareLaunchArgument('use_imu', default_value='false',
                              description='Subscribe to /imu/data in odometry node'),
        DeclareLaunchArgument('publish_tf', default_value='true',
                              description='Broadcast odom->base_link TF from odometry node'),

        # --- Joint State Node ---
        Node(
            package='ugv_localization',
            executable='joint_state_node',
            name='joint_state_node',
            output='screen',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        ),

        # --- IMU Node ---
        Node(
            package='ugv_localization',
            executable='imu_node',
            name='imu_node',
            output='screen',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        ),

        # --- Odometry Node ---
        Node(
            package='ugv_localization',
            executable='odometry_node',
            name='odometry_node',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'use_imu': LaunchConfiguration('use_imu'),
                'publish_tf': LaunchConfiguration('publish_tf'),
                # TODO: set these from a YAML param file for hardware-specific values
                # 'wheel_radius': 0.05,
                # 'wheel_base': 0.3,
                # 'encoder_ticks_per_rev': 1440,
                # 'left_joint_name': 'left_wheel_joint',
                # 'right_joint_name': 'right_wheel_joint',
            }],
        ),

        # --- EKF (robot_localization) ---
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[
                ekf_config,
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
            ],
            condition=IfCondition(LaunchConfiguration('use_ekf')),
        ),
    ])
