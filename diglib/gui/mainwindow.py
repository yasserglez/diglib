# -*- coding: utf-8 -*-

import gtk

from diglib.gui.xmlwidget import XMLWidget
from diglib.gui.aboutdialog import AboutDialog


class MainWindow(XMLWidget):

    def __init__(self, library):
        super(MainWindow, self).__init__('main_window')
        self._library = library
        
    def on_main_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_quit_menuitem_activate(self, widget, data=None):
        self.destroy()
        
    def on_about_menuitem_activate(self, widget, data=None):
        dialog = AboutDialog()
        dialog.run()
        dialog.destroy()
