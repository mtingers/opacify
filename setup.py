from distutils.core import setup
import setuptools 

setup(
    name='Opacify',
    version='0.2.3',
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
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: System :: Archiving :: Mirroring',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)

