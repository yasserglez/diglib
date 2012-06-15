# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011-2012 Yasser González Fernández <ygonzalezfernandez@gmail.com>
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

from diglib.core.util import text_from_tags, tags_from_text


class EditTagsDialog(gtk.Dialog):

    def __init__(self, tags):
        super(EditTagsDialog, self).__init__()
        # Other instance attributes.
        self._tags = tags
        # Initialize widgets.
        self.set_title('Edit Tags')
        self.set_resizable(False)
        self.set_modal(True)
        self.set_border_width(12)
        self.set_default_response(gtk.RESPONSE_OK)
        content_area = self.get_content_area()
        content_area.set_spacing(18)
        hbox = gtk.HBox()
        hbox.set_spacing(12)
        label = gtk.Label('Tags:')
        hbox.pack_start(label)
        tags_entry = gtk.Entry()
        tags_entry.connect('changed', self.on_tags_entry_changed)
        tags_entry.set_width_chars(40)
        tags_entry.set_text(text_from_tags(self._tags))
        hbox.pack_start(tags_entry)
        content_area.pack_end(hbox)
        content_area.show_all()
        self.add_button('Cancel', gtk.RESPONSE_CANCEL)
        self._add_button = self.add_button('Edit', gtk.RESPONSE_OK)
        self._add_button.set_property('can-focus', True)
        self._add_button.grab_focus()
        self._add_button.set_property('can-default', True)
        self._add_button.grab_default()

    def get_tags(self):
        return self._tags

    def on_tags_entry_changed(self, tags_entry):
        self._tags = tags_from_text(tags_entry.get_text())
