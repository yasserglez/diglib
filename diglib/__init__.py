# -*- coding: utf-8 -*-

from diglib.core import DigitalLibrary
from diglib.core.index import XapianIndex
from diglib.core.database import SQLAlchemyDatabase
from diglib.gui import GUI


NAME = 'Digital Library'
DESCRIPTION = 'Manage a collection of digital documents.'
AUTHOR = 'Yasser González-Fernández <ygonzalezfernandez@gmail.com>'
COPYRIGHT = 'Copyright © 2011 Yasser González-Fernández'
VERSION = '0.1.0'


def main(library_dir):
    try:
        library = DigitalLibrary(library_dir, XapianIndex, SQLAlchemyDatabase)
        gui = GUI(library)
        gui.start()
        library.close()
    except KeyboardInterrupt:
        pass
