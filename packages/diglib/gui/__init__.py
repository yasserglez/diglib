# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011-2013 Yasser González Fernández <ygonzalezfernandez@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

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
                         'diglib-document-tag', 'diglib-directory-add'):
            icon_path = get_image('%s.svg' % stock_id)
            icon_set = gtk.IconSet(gtk.gdk.pixbuf_new_from_file(icon_path))
            icon_factory.add(stock_id, icon_set)
        icon_factory.add_default()

    def start(self):
        self._main_window.show()
        gtk.main()
