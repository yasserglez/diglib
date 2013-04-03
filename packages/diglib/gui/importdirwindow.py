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

import os

import gtk
import gobject

from diglib.core import error
from diglib.core.util import tags_from_text
from diglib.gui.xmlwidget import XMLWidget


class ImportDirectoryWindow(XMLWidget):
    
    TREEVIEW_COLUMN_NAME = 0
    TREEVIEW_COLUMN_PATH = 1
    TREEVIEW_COLUMN_RESULT = 2

    def __init__(self, library):
        super(ImportDirectoryWindow, self).__init__('import_dir_window')
        # Instance attributes for widgets.
        self._import_dir_window = self._builder.get_object('import_dir_window')
        self._progressbar = self._builder.get_object('progressbar')
        self._table = self._builder.get_object('table')
        self._hbuttonbox = self._builder.get_object('hbuttonbox')
        self._treeview = self._builder.get_object('treeview')
        self._progress_vbox = self._builder.get_object('progress_vbox')
        self._tags_entry = self._builder.get_object('tags_entry')
        self._filechooserbutton = self._builder.get_object('filechooserbutton')
        self._delete_checkbutton = self._builder.get_object('delete_checkbutton')
        self._liststore = gtk.ListStore(str, str, str)
        # Other instance attributes.
        self._library = library
        self._exit = False
        self._doc_paths = None
        self._doc_tags = None
        # Initialize widgets.
        self._init_treeview()

    def _init_treeview(self):
        self._treeview.set_model(self._liststore)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('File', renderer, text=self.TREEVIEW_COLUMN_NAME)
        self._treeview.append_column(column)
        column = gtk.TreeViewColumn('Result', renderer, text=self.TREEVIEW_COLUMN_RESULT)
        self._treeview.append_column(column)
        self._treeview.set_tooltip_column(self.TREEVIEW_COLUMN_PATH)
        self._treeview.columns_autosize()
        self._treeview.show_all()

    def run(self):
        self._import_dir_window.show()
        self._import_dir_window.connect('destroy', self.on_import_dir_window_destroy)
        while not self._exit:
            gtk.main_iteration(True)
        return gtk.RESPONSE_CANCEL if (self._doc_paths is None) else gtk.RESPONSE_OK

    def on_import_dir_window_destroy(self, widget):
        self._exit = True

    def on_import_button_clicked(self, button):
        dir_path = self._filechooserbutton.get_filename()
        self._doc_tags = tags_from_text(self._tags_entry.get_text())
        # Disable all widgets but the ones reporting progress.
        self._table.set_sensitive(False)
        self._progress_vbox.set_sensitive(True)
        self._hbuttonbox.set_sensitive(False)
        self._delete_checkbutton.set_sensitive(False)
        # Generating the list of documents to be imported.
        self._doc_paths = []
        for dirpath, _, filenames in os.walk(dir_path):
            self._doc_paths.extend([os.path.join(dirpath, name) for name in filenames])
        self._total_docs = len(self._doc_paths)
        self._progressbar.set_fraction(0)
        self._progressbar.set_text('Importing document %s of %s' % (1, self._total_docs))        
        gobject.idle_add(self._import_docs)

    def on_cancel_button_clicked(self, button):
        self.destroy()

    def _import_docs(self):
        if not self._doc_paths:
            self._progressbar.set_fraction(1.0)
            self._progressbar.set_text('Completed')
            return False # Finished importing documents.
        doc_path = self._doc_paths.pop()
        current_doc = self._total_docs - len(self._doc_paths)
        self._progressbar.set_fraction(current_doc / float(self._total_docs))
        self._progressbar.set_text('Importing document %s of %s' %
                                   (current_doc + 1, self._total_docs))
        try:
            self._library.add_doc(doc_path, self._doc_tags)
        except error.DocumentDuplicatedExact:
            result = 'The document is already in the library.'
            if self._delete_checkbutton.get_active():
                os.remove(doc_path)
        except error.DocumentDuplicatedSimilar:
            result = 'A similar document is already in the library.'
        except error.DocumentNotRetrievable:
            result = 'The document is not retrievable.'
        except error.DocumentNotSupported:
            result = 'The format of the document not supported.'
        except:
            result = 'Unexpected error.'
        else:
            result = 'The document was imported.'
            if self._delete_checkbutton.get_active():
                os.remove(doc_path)            
        self._liststore.append([os.path.basename(doc_path), doc_path, result])
        # Make the last row visible.
        last_path = (len(self._liststore) - 1, )
        self._treeview.scroll_to_cell(last_path)
        return True # Continue importing files.
