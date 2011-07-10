# -*- coding: utf-8 -*-

import os
import time
import threading

import gtk
import gobject

from diglib.core.util import tags_from_text
from diglib.gui.xmlwidget import XMLWidget


class ImportDirectoryWindow(XMLWidget):
    
    def __init__(self, library):
        super(ImportDirectoryWindow, self).__init__('import_dir_window')
        # Instance attributes for widgets.
        self._progressbar = self._builder.get_object('progressbar')
        self._table = self._builder.get_object('table')
        self._hbuttonbox = self._builder.get_object('hbuttonbox')
        self._treeview = self._builder.get_object('treeview')
        self._progress_vbox = self._builder.get_object('progress_vbox')
        self._liststore = gtk.ListStore(str, str, str)
        # Other instance attributes.
        self._library = library
        # Initialize complex widgets.
        self._init_treeview()

    def _init_treeview(self):
        COLUMN_NAME, COLUMN_PATH, COLUMN_RESULT = 0, 1, 2
        self._treeview.set_model(self._liststore)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('File', renderer, text=COLUMN_NAME)
        self._treeview.append_column(column)
        column = gtk.TreeViewColumn('Result', renderer, text=COLUMN_RESULT)
        self._treeview.append_column(column)
        self._treeview.set_tooltip_column(COLUMN_PATH)
        self._treeview.columns_autosize()
        self._treeview.show_all()

    def on_import_button_clicked(self, button):
        filechooser = self._builder.get_object('filechooserbutton')
        entry = self._builder.get_object('tags_entry')
        dir_path = filechooser.get_filename()
        tags = tags_from_text(entry.get_text())
        # Disable all widgets but the ones reporting progress.
        self._progress_vbox.set_sensitive(True)
        self._table.set_sensitive(False)
        self._hbuttonbox.set_sensitive(False)
        # Start the thread importing files.
        self._thread = threading.Thread(target=self._import_docs, args=(dir_path, tags))
        self._thread.start()

    def on_cancel_button_clicked(self, button):
        self.destroy()

    def _import_docs(self, dir_path, tags):
        # Generating the list of documents to known the total number of documents.
        doc_paths = []
        for dirpath, _, filenames in os.walk(dir_path):
            doc_paths.extend([os.path.join(dirpath, name) for name in filenames])
        total_docs = len(doc_paths)
        # Importing each document (updating the widgets reporting progress).
        for i, doc_path in enumerate(doc_paths):
            with gtk.gdk.lock:
                gobject.idle_add(self._update_progressbar, i + 1, total_docs)
            try:
                time.sleep(0.5)
#                self._library.add_doc(doc_path, tags)
            except Exception:
                result = 'Unexpected error'
            else:
                result = 'Imported'
            with gtk.gdk.lock:
                gobject.idle_add(self._update_treeview, doc_path, result)
        with gtk.gdk.lock:
            self._progressbar.set_fraction(1.0)
            self._progressbar.set_text('Completed')

    def _update_progressbar(self, current_doc, total_docs):
        self._progressbar.set_fraction(current_doc / float(total_docs))
        self._progressbar.set_text('Importing document %s of %s' %
                                   (current_doc, total_docs))

    def _update_treeview(self, doc_path, result):
        self._liststore.append([os.path.basename(doc_path), doc_path, result])
        path_last = (len(self._liststore) - 1, )
        self._treeview.scroll_to_cell(path_last)
