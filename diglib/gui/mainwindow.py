# -*- coding: utf-8 -*-

from diglib.gui.xmlwidget import XMLWidget


class MainWindow(XMLWidget):

    def __init__(self, library):
        super(MainWindow, self).__init__('main_window')
        self._library = library
