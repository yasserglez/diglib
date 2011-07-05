# -*- coding: utf-8 -*-

import gtk

from diglib.gui.xmlwidget import XMLWidget
from diglib.gui.aboutdialog import AboutDialog
from diglib.gui.searchentry import SearchEntry


class MainWindow(XMLWidget):

    def __init__(self, library):
        super(MainWindow, self).__init__('main_window')
        self._library = library
        self._init_toolbar()
        
    def _init_toolbar(self):
        # The ombo box with the size of the icons.
        iconsize_toolitem = self._builder.get_object('iconsize_toolitem')
        iconsize_combobox = gtk.combo_box_new_text()
        iconsize_combobox.append_text('Small Icons')
        iconsize_combobox.append_text('Normal Icons')
        iconsize_combobox.append_text('Large Icons')
        iconsize_combobox.set_active(1)
        iconsize_toolitem.add(iconsize_combobox)
        iconsize_toolitem.show_all()
        # The search text entry.
        search_toolitem = self._builder.get_object('search_toolitem')
        search_entry = SearchEntry()
        search_entry.set_width_chars(25)
        search_entry.connect('activate-timeout', self.on_search_entry_activate_timeout)
        search_toolitem.add(search_entry)
        search_toolitem.show_all()

    def on_main_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_close_menuitem_activate(self, widget, data=None):
        self.destroy()

    def on_about_menuitem_activate(self, widget, data=None):
        dialog = AboutDialog()
        dialog.run()
        dialog.destroy()

    def on_search_entry_activate_timeout(self, widget, data=None):
        query = widget.get_text()
        print query

    def on_importfile(self, widget, data=None):
        print 'importfile'

    def on_importdir(self, widget, data=None):
        print 'importdir'

    def on_addtag(self, widget, data=None):
        print 'addtag'

    def on_renametag(self, widget, data=None):
        print 'renametag'

    def on_deletetag(self, widget, data=None):
        print 'deletetag'

    def on_opendoc(self, widget, data=None):
        print 'opendoc'

    def on_copydoc(self, widget, data=None):
        print 'copydoc'

    def on_deletedoc(self, widget, data=None):
        print 'deletedoc'

    def on_docproperties(self, widget, data=None):
        print 'docproperties'
