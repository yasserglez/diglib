# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011 Yasser González-Fernández <ygonzalezfernandez@gmail.com>
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

# Search entry with timeout based on the implementation of ubuntu-software-center.

import gtk
import gobject


class SearchEntry(gtk.Entry):

    __gsignals__ = {
        'activate-timeout': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, timeout=500):
        super(SearchEntry, self).__init__()
        self._changed_handler = self.connect_after('changed', self.on_changed)
        self.connect('icon-press', self.on_icon_press)
        self.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, gtk.STOCK_FIND)
        self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)
        self._timeout = timeout
        self._timeout_id = 0

    def on_icon_press(self, widget, icon, event):
        # Emit the activate-timeout signal without any timeout when
        # the clear button is clicked.
        if icon == gtk.ENTRY_ICON_SECONDARY:
            self._clear_without_signal()
            self.grab_focus()
            self.emit('activate-timeout')
        elif icon == gtk.ENTRY_ICON_PRIMARY:
            self.select_region(0, -1)
            self.grab_focus()

    def on_changed(self, widget):
        # Call the actual search method after a timeout
        # to allow the user to enter a longer search term.
        self._check_style()
        if self._timeout_id > 0:
            gobject.source_remove(self._timeout_id)
        gobject.timeout_add(self._timeout, self._timeout_callback)

    def _timeout_callback(self):
        self._timeout_id = 0
        self.emit('activate-timeout')
        return False # Do not call the function again.

    def _clear_without_signal(self):
        # Clear and do not send a term-changed signal.
        self.handler_block(self._changed_handler)
        self.set_text('')
        self._check_style()
        self.handler_unblock(self._changed_handler)

    def _check_style(self):
        # Show the clear icon whenever the field is not empty.
        if self.get_text():
            self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, gtk.STOCK_CLEAR)
            # Reverse the icon in a RTL environment.
            if self.get_direction() == gtk.TEXT_DIR_RTL:
                pixbuf = self.get_icon_pixbuf(gtk.ENTRY_ICON_SECONDARY).flip(True)
                self.set_icon_from_pixbuf(gtk.ENTRY_ICON_SECONDARY, pixbuf)
        else:
            self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)
