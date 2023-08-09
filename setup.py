from setuptools import setup, find_packages
from Cython.Build import cythonize

setup(
    name = "BaconPGCSummerJam2023",
    ext_modules = cythonize("*.pyx"),
    packages = find_packages(),
    package_dir = {"BaconPGCSummerJam2023":""}
)