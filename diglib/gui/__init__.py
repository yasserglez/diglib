# -*- coding: utf-8 -*-

import gtk

from diglib.gui.util import get_image
from diglib.gui.mainwindow import MainWindow


class GUI(object):

    def __init__(self, library):
        super(GUI, self).__init__()
        self._init_icons()
        self._main_window = MainWindow(library)

    def _init_icons(self):
        gtk.window_set_default_icon_from_file(get_image('diglib.svg'))
        icon_factory = gtk.IconFactory()
        for stock_id in ('diglib-document-add', 'diglib-document-open', 
                         'diglib-document-copy', 'diglib-document-delete', 
                         'diglib-tag-delete', 'diglib-tag-add',
                         'diglib-directory-add'):
            icon_path = get_image('%s.svg' % stock_id)
            icon_set = gtk.IconSet(gtk.gdk.pixbuf_new_from_file(icon_path))
            icon_factory.add(stock_id, icon_set)
        icon_factory.add_default()

    def start(self):
        self._main_window.show()
        gtk.main()
