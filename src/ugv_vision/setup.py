import os
from glob import glob
from setuptools import setup

package_name = 'ugv_vision'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='trekker',
    maintainer_email='todo@example.com',
    description='Inspection trigger, image capture, and hazard detection for UGV Beast',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'inspection_trigger_node = ugv_vision.inspection_trigger_node:main',
            'image_capture_node = ugv_vision.image_capture_node:main',
            'hazard_detector_node = ugv_vision.hazard_detector_node:main',
        ],
    },
)
