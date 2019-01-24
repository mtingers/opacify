from distutils.core import setup
import setuptools 

setup(
    name='Opacify',
    version='0.1.2',
    author='Matth Ingersoll',
    author_email='matth@mtingers.com',
    packages=['opacify',],
    license='BSD 2-Clause License',
    long_description=open('README.md').read(),
    url='https://github.com/mtingers/opacify',
    scripts=['bin/opacify',],
    install_requires=[
        "requests",
    ],
)

