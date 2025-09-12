from setuptools import setup, find_packages
import os
from glob import glob

setup(
    name='ur_robot_server',
    version='0.0.1',
    packages=find_packages(where='ur_robot_server'),

    entry_points={
        'console_scripts': [
            'robot_server = ur_robot_server.robot_server:main',
            'joint_trajectory_command_handler = ur_robot_server.joint_trajectory_command_handler:main',
        ],
    },
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + 'ur_robot_server']),
        ('share/' + 'ur_robot_server', ['package.xml']),
        (os.path.join('share', 'ur_robot_server', 'launch'),
            glob('launch/*.launch.py')),
    ],

    install_requires=[],
    zip_safe=True,
)