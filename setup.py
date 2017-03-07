import os
import sys

from pip.req import parse_requirements
from pip.download import PipSession
from setuptools import find_packages

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# reading requirements
install_reqs = parse_requirements('requirements.txt', session=PipSession())
reqs = [str(ir.req) for ir in install_reqs]
sys.path.insert(0, os.path.dirname(__file__))
version = '0.2'
setup(
    name='cappy',
    version=version,
    packages=find_packages(),
    install_requires=reqs,
    long_description="CAchingProxyinPython is a file based python proxy based on Sharebear's simple python caching proxy",
    description='A simple file based python poxy',
    keywords = ['cappy', 'proxy', 'http'],
    url='https://github.com/CompileInc/cappy',
    download_url = 'https://github.com/CompileInc/cappy/archive/v{version}.tar.gz'.format(version=version),
    author='Compile Inc',
    author_email='dev@compile.com',
    entry_points='''
        [console_scripts]
        cappy=cappy.cappy:cli
    '''
)
