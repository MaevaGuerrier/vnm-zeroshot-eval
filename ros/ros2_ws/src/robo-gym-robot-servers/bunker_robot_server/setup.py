#!/usr/bin/env python

from setuptools import setup
import os
from glob import glob

from setuptools import setup
package_name = 'bunker_robot_server'
setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'robot_server = bunker_robot_server.robot_server:main',
        ],
    },
)

