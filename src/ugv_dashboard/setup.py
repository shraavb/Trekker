import os
from glob import glob
from setuptools import setup

package_name = 'ugv_dashboard'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='trekker',
    maintainer_email='todo@example.com',
    description='MQTT bridge and dashboard integration for UGV Beast inspection rover',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mqtt_bridge_node = ugv_dashboard.mqtt_bridge_node:main',
        ],
    },
)
