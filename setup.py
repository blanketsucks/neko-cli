from setuptools import find_packages, setup

packages = find_packages()

with open('README.md', 'r') as file:
    description = file.read()

with open('requirements.txt', 'r') as file:
    requirements = file.readlines()

setup(
    name='neko',
    version='1.2.0',
    author='blanketsucks',
    url='https://github.com/blanketsucks/neko-cli',
    packages=packages,
    entry_points={
        'console_scripts': ['neko-cli = neko.__main__:main', 'neko-viewer = neko.viewer:main'],
    },
    python_requires='>=3.8',
    description='a NSFW/SFW image downloader.',
    long_description=description,
    install_requires=requirements,
)