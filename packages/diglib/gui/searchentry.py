# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011-2012 Yasser González-Fernández <ygonzalezfernandez@gmail.com>
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


class SearchEntry(gtk.Entry):

    def __init__(self):
        super(SearchEntry, self).__init__()
        self.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, gtk.STOCK_FIND)
        self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)
        self._changed_handler = self.connect_after('changed', self.on_changed)
        self.connect('icon-press', self.on_icon_press)

    def on_icon_press(self, widget, icon, event):
        if icon == gtk.ENTRY_ICON_SECONDARY:
            self.handler_block(self._changed_handler)
            self.set_text('')
            self._check_style()
            self.handler_unblock(self._changed_handler)
            self.grab_focus()
            self.emit('activate')
        elif icon == gtk.ENTRY_ICON_PRIMARY:
            self.select_region(0, -1)
            self.grab_focus()

    def on_changed(self, widget):
        self._check_style()

    def _check_style(self):
        # Show the clear icon whenever the field is not empty.
        if self.get_text():
            self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, gtk.STOCK_CLEAR)
        else:
            self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)
