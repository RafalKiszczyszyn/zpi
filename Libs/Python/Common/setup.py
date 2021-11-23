from setuptools import find_packages, setup

setup(
    name='zpi-common',
    packages=find_packages(exclude=[]),
    version='0.1.0',
    description='ZPI Common Libraries',
    author='Rafał Kiszczyszyn',
    license='MIT',
    install_requires=['pika-1.2.0']
)