import os
import sys

from setuptools import setup, find_packages
from setuptools.command.install import install

# circleci.py version
VERSION = "0.0.4"

with open("README.md", "r") as fh:
    long_description = fh.read()


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


setup(
    name="atko",
    version=VERSION,
    py_modules=['atko'],
    entry_points='''
        [console_scripts]
        atko=atkocli:cli
    ''',
    author="Indranil Jha",
    author_email="indranilokg@gmail.com",
    description="CLI tool for Okta",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/indranilokg/atko-cli",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    license="MIT",
    keywords='okta cli api',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    cmdclass={
        'verify': VerifyVersionCommand,
    },
    install_requires=[
        'click>=7.0',
        'requests>=2.23.0',
        'pandas==1.1.3',
        'jwcrypto==0.8',
        'py_jwt_verifier==0.7.1',
        'pyjwt==1.7.1',
        'prettytable==1.0.1'
    ],
)
