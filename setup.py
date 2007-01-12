from distutils.core import setup
from doc import make_doc_command
from sys import version

# Metadata
NAME="pymsn"
VERSION="0.2.1"
DESCRIPTION="Python msn client library"
AUTHOR="Ali Sabil"
AUTHOR_EMAIL="ali.sabil@gmail.com"
URL="http://telepathy.freedesktop.org/wiki/Pymsn",
LICENSE="GNU GPL",


# compatibility with python < 2.2.3
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

# Documentation
doc_commands = {
    'build_doc': make_doc_command(
         name='pymsn',
         description='Python msn client library',
         url=URL,
         output='pymsn',
         post='doc/fix_encoding.sh doc/pymsn/*.html',
         packages='pymsn')
}

# Setup
setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      license=LICENSE,
      platforms=["any"],
      packages=["pymsn", "pymsn.gio"],
      cmdclass=doc_commands,
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
