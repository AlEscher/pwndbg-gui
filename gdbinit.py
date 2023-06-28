import sys
from os import path

# Adding directory to gdb sys.path to allow the package to be imported
directory, file = path.split(__file__)
directory = path.expanduser(directory)
directory = path.abspath(directory)
sys.path.append(directory)
