# -*- coding: utf-8 -*-

import os

import gtk

from diglib.gui.mainwindow import MainWindow


class GUI(object):

    def __init__(self, library):
        super(GUI, self).__init__()
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diglib.svg')
        gtk.window_set_default_icon_from_file(icon_path)
        self._main_window = MainWindow(library)

    def start(self):
        self._main_window.show()
        gtk.main()
