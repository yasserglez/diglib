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

import gtk


class AddTagDialog(gtk.Dialog):

    def __init__(self):
        super(AddTagDialog, self).__init__()
        self.set_title('Add Tag')
        self.set_resizable(False)
        self.set_modal(True)
        self.set_border_width(12)
        content_area = self.get_content_area()
        content_area.set_spacing(18)
        hbox = gtk.HBox()
        hbox.set_spacing(12)
        label = gtk.Label('Tag:')
        hbox.pack_start(label)
        tag_entry = gtk.Entry()
        tag_entry.connect('changed', self.on_tag_entry_changed)
        hbox.pack_start(tag_entry)
        content_area.pack_end(hbox)
        hbox.show_all()
        self.add_button('Cancel', gtk.RESPONSE_CANCEL)
        self._add_button = self.add_button('Add', gtk.RESPONSE_ACCEPT)
        self._add_button.set_property('can-default', True)
        self._add_button.grab_default()
        self._add_button.set_sensitive(False)
        self.set_default_response(gtk.RESPONSE_ACCEPT)
        self._tag = None

    def get_tag(self):
        return self._tag

    def on_tag_entry_changed(self, entry):
        self._tag = entry.get_text().strip()
        if self._tag:
            self._add_button.set_sensitive(True)
