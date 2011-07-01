# -*- coding: utf-8 -*-

from diglib.core import DigitalLibrary
from diglib.core.index.xapian import XapianIndex
from diglib.core.database.sqlalchemy import SQLAlchemyDatabase
from diglib.gui import GUI


def main(library_dir):
    try:
        library = DigitalLibrary(library_dir, XapianIndex, SQLAlchemyDatabase)
        gui = GUI(library)
        gui.start()
        library.close()
    except KeyboardInterrupt:
        pass
