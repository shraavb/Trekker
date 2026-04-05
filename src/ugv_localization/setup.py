import os
from glob import glob
from setuptools import setup

package_name = 'ugv_localization'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='trekker',
    maintainer_email='todo@example.com',
    description='Odometry and sensor fusion for UGV Beast inspection rover',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'odometry_node = ugv_localization.odometry_node:main',
            'joint_state_node = ugv_localization.joint_state_node:main',
            'imu_node = ugv_localization.imu_node:main',
        ],
    },
)
