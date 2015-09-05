# -*- coding: utf-8 -*-
#
# diglib: Personal digital document management software.
# Copyright (C) 2011-2015 Yasser Gonzalez <yasserglez@gmail.com>
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

from diglib.core.util import tags_from_text
from diglib.gui.xmlwidget import XMLWidget


class ImportFileDialog(XMLWidget):

    def __init__(self):
        super(ImportFileDialog, self).__init__('import_file_dialog')
        # Instance attributes for widgets.
        self._import_button = self._builder.get_object('import_button')
        # Other instance attributes.
        self._filename = None
        self._tags = set()

    def get_filename(self):
        return self._filename

    def get_tags(self):
        return self._tags

    def on_filechooserbutton_file_set(self, filechooserbutton):
        self._filename = filechooserbutton.get_filename()
        self._import_button.set_sensitive(True)

    def on_tags_entry_changed(self, entry):
        self._tags = tags_from_text(entry.get_text())
