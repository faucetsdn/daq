import os
from setuptools import setup

version = os.popen('git describe').read().strip()
version_content = f'''"""DAQ version file"""

__version__ = '{version}'
'''
with open('daq/__version__.py', 'w+') as version_file:
    version_file.write(version_content)

setup(
    name='daq',
    setup_requires=['pbr>=1.9', 'setuptools>=17.1'],
    pbr=True
)
