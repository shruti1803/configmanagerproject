# File: setup.py
# Package setup for Configuration Management System
from setuptools import setup, find_packages

setup(
    name="config-manager",
    version="1.0.0",
    description="A comprehensive configuration management system for multi-environment applications",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "config-manager=src.config_manager:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)