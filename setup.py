from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Pipflow',
    version='0.1.1',
    description='Python Distribution Utilities',
    author='Michael Martinez',
    author_email='imichael@pm.me',
    url='https://github.com/iMerica/pipflow',
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='Package Managers',
    packages=['pipflow', 'pipflow.src'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.5',
    install_requires=['cleo>=0.8.1', 'requests'],
    entry_points={
        'console_scripts': [
            'pipflow = pipflow.__main__:main'
        ]
    }
)
