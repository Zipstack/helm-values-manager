"""Setup script for helm-values-manager."""

from setuptools import find_packages, setup

setup(
    packages=find_packages(include=["helm_values_manager", "helm_values_manager.*"]),
)
