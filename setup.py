from distutils.core import setup
import os


# Metadata
NAME = "pymsn"
VERSION = "0.3.0"
DESCRIPTION = "Python msn client library"
AUTHOR = "Ali Sabil"
AUTHOR_EMAIL = "ali.sabil@gmail.com"
URL = "http://telepathy.freedesktop.org/wiki/Pymsn"
LICENSE = "GNU GPL"

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
pymsn_dir = os.path.join(root_dir, 'pymsn')
pieces = fullsplit(root_dir)
if pieces[-1] == '':
    len_root_dir = len(pieces) - 1
else:
    len_root_dir = len(pieces)

for dirpath, dirnames, filenames in os.walk(pymsn_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'):
            del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)[len_root_dir:]))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

# Setup
setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      license=LICENSE,
      platforms=["any"],
      packages=packages,
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
