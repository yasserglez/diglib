# -*- coding: utf-8 -*-

# Search entry with timeout based on the implementation of the Ubuntu Software Center.

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
        gobject.timeout_add(self._timeout, self._timeout_callback)

    def _timeout_callback(self):
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
