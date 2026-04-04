"""Launch file for ugv_navigation: waypoint patrol node."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),

        # TODO: include nav2_bringup navigation_launch.py here when Nav2 is installed
        # IncludeLaunchDescription(
        #     PythonLaunchDescriptionSource([
        #         FindPackageShare('nav2_bringup'), '/launch/navigation_launch.py'
        #     ]),
        #     launch_arguments={'use_sim_time': LaunchConfiguration('use_sim_time')}.items(),
        # ),

        Node(
            package='ugv_navigation',
            executable='waypoint_patrol_node',
            name='waypoint_patrol_node',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                # TODO: define real patrol waypoints [x1, y1, yaw1, x2, y2, yaw2, ...]
                'waypoints': [0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 2.0, 1.57],
                'loop': False,
            }],
        ),
    ])
