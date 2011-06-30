# -*- coding: utf-8 -*-

import logging

from diglib.gui import GUI
from diglib.core import DigitalLibrary


def main(library_dir):
    try:
        library = DigitalLibrary(library_dir)
        gui = GUI(library)
        gui.start()
        library.close()
    except KeyboardInterrupt:
        pass
