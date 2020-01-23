import os
import setuptools

own_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(own_dir, 'README.md')) as f:
    long_description = f.read()



setuptools.setup(
    name='temper-py',
    version='0.0.1',
    author='urwen',
    description='Reads temperature data from misc. "TEMPer" devices with minimal dependencies',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ccwienk/temper',
    py_modules=['temper'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
)
