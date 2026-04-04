"""
Top-level bringup launch file for Trekker.

Composes localization, navigation, vision, and dashboard launches
with top-level arguments for toggling subsystems.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    loc_share = get_package_share_directory('ugv_localization')
    nav_share = get_package_share_directory('ugv_navigation')
    vis_share = get_package_share_directory('ugv_vision')

    return LaunchDescription([
        # --- Top-level arguments ---
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='Use simulation clock (for rosbag playback)'),
        DeclareLaunchArgument('use_ekf', default_value='false',
                              description='Enable EKF sensor fusion'),
        DeclareLaunchArgument('enable_nav', default_value='false',
                              description='Enable Nav2 navigation + patrol'),
        DeclareLaunchArgument('enable_vision', default_value='true',
                              description='Enable vision inspection pipeline'),

        # --- Localization ---
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(loc_share, 'launch', 'localization.launch.py')
            ),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'use_ekf': LaunchConfiguration('use_ekf'),
            }.items(),
        ),

        # --- Navigation ---
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav_share, 'launch', 'navigation.launch.py')
            ),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
            condition=IfCondition(LaunchConfiguration('enable_nav')),
        ),

        # --- Vision ---
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(vis_share, 'launch', 'vision.launch.py')
            ),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
            condition=IfCondition(LaunchConfiguration('enable_vision')),
        ),

        # --- MQTT Dashboard Bridge ---
        Node(
            package='ugv_dashboard',
            executable='mqtt_bridge_node',
            name='mqtt_bridge_node',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                # TODO: set Cyberwave MQTT broker credentials
                # 'mqtt_host': 'broker.cyberwave.com',
                # 'mqtt_port': 1883,
                # 'mqtt_username': '',
                # 'mqtt_password': '',
            }],
        ),
    ])
