# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('gifmaze/version.py') as f:
    exec(f.read())


setup(
    name='gifmaze',
    version=__version__,
    description='Make GIF animations of maze generation and maze solving algorithms with pure Python.',
    author='Zhao Liang',
    author_email='mathzhaoliang@gmail.com',
    url='https://github.com/neozhaoliang/gifmaze',
    license='MIT',
    packages=find_packages()
    )
