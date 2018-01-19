import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "matrix-creator-client",
    version = "0.0.1",
    author = "David Randler",
    author_email = "david.randler@gmail.com",
    description = ("A client for accessing and controlling a Matrix Creator device."),
    license = "MIT License",
    keywords = "matrix creator client zeromq malos",
    url = "http://packages.python.org/an_example_pypi_project",
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],
)
  