# -*- coding: utf-8 -*-

from diglib.core.util import tags_from_text
from diglib.gui.xmlwidget import XMLWidget


class ImportDocumentDialog(XMLWidget):
    
    def __init__(self):
        super(ImportDocumentDialog, self).__init__('import_doc_dialog')
        self._filename = None
        self._tags = None

    def get_filename(self):
        return self._filename

    def get_tags(self):
        return self._tags

    def on_filechooserbutton_file_set(self, filechooserbutton):
        self._filename = filechooserbutton.get_filename()
        button = self._builder.get_object('import_button')
        button.set_sensitive(True)

    def on_tags_entry_changed(self, entry):
        self._tags = tags_from_text(entry.get_text())
