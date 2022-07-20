# setup.py

from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='ProxyEater',
    version='1.2.1',
    author='CodeWriter21',
    author_email='CodeWriter21@gmail.com',
    description='A Python Proxy Scraper for gathering fresh proxies.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/MPCodeWriter21/ProxyEater',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ProxyEater=ProxyEater.__main__:main'
        ]
    },
    install_requires=['requests', 'beautifulsoup4', 'lxml', 'pandas', 'html5lib', 'log21', 'importlib_resources'],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    include_package_data=True
)
