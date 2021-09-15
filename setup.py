from __future__ import absolute_import
import os
import sys

try:
    from pip._internal.req import parse_requirements
except ImportError:
    # pip < 10
    from pip.req import parse_requirements
try:
    from pip._internal.network.session import PipSession
except ImportError:
    try:
        from pip._internal.download import PipSession
    except ImportError:
        # pip < 10
        from pip.download import PipSession


from setuptools import find_packages

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


# reading requirements
install_reqs = parse_requirements('requirements.txt', session=PipSession())
try:
    requirements = [str(ir.req) for ir in install_reqs]
except AttributeError:
    # pip > 20
    requirements = [str(ir.requirement) for ir in install_reqs]

sys.path.insert(0, os.path.dirname(__file__))
version = '1.2.3'
setup(
    name='cappy',
    version=version,
    packages=find_packages(),
    install_requires=requirements,
    license='MIT',
    long_description="CAchingProxyinPython is a file based python proxy based on Sharebear's simple python caching proxy",
    description='A simple file based python poxy',
    keywords=['cappy', 'proxy', 'http'],
    url='https://github.com/CompileInc/cappy',
    download_url='https://github.com/CompileInc/cappy/archive/v{version}.tar.gz'.format(version=version),
    author='Compile Inc',
    author_email='dev@compile.com',
    entry_points='''
        [console_scripts]
        cappy=cappy.cappy:cli
    '''
)
