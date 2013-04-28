#! /usr/bin/env python

from docopt import docopt
from path import path
from utils import rename

if __name__ == "__main__":
    doc = """Renamer.

    Renames files within a directory
    Knows how to rename files from different sites such as youtube, vimeo,
    piratebay etc.

    Usage:
    rename.py [--debug] <directories>...
    rename.py (-h | --help)
    rename.py --version

    Options:
    -h --help     Show this screen.
    --version     Show version.
    --debug       Debug mode, no files are actually renamed.
    """

    args = docopt(doc, version='Renamer 1.0 Beta')
    DEBUG = args["--debug"]

    for d in args["<directories>"]:
        d = path(d)
        with d:
            for f in d.files():
                rename(f, DEBUG)
