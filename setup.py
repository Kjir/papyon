from distutils.core import setup
from sys import version

# Metadata
NAME = "pymsn"
VERSION = "0.3.0"
DESCRIPTION = "Python msn client library"
AUTHOR = "Ali Sabil"
AUTHOR_EMAIL = "ali.sabil@gmail.com"
URL = "http://telepathy.freedesktop.org/wiki/Pymsn"
LICENSE = "GNU GPL"

# Setup
setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      license=LICENSE,
      platforms=["any"],
      packages=["pymsn"],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Telecommunications Industry',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: POSIX',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python',
          'Topic :: Communications :: Chat',
          'Topic :: Communications :: Telephony',
          'Topic :: Internet',
          'Topic :: Software Development :: Libraries :: Python Modules'
          ])
