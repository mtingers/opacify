from distutils.core import setup
import setuptools 

setup(
    name='Opacify',
    version='0.1.3',
    author='Matth Ingersoll',
    author_email='matth@mtingers.com',
    packages=['opacify',],
    license='BSD 2-Clause License',
    long_description=open('README.md').read(),
    url='https://github.com/mtingers/opacify',
    install_requires=[
        "requests",
    ],
    #scripts=['bin/opacify',],
    entry_points={
        'console_scripts': ['opacify=opacify.opacify_cli:main',],
    },
)

