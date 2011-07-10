# -*- coding: utf-8 -*-

import gtk


class AddTagDialog(gtk.Dialog):
    
    def __init__(self, parent):
        super(AddTagDialog, self).__init__(parent=parent)
        self.set_title('Add Tag')
        self.set_has_separator(False)
        self.set_modal(True)
        self.set_resizable(False)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_border_width(12)
        content_area = self.get_content_area()
        content_area.set_spacing(18)
        hbox = gtk.HBox()
        hbox.set_spacing(12)
        label = gtk.Label('Tag:')
        hbox.pack_start(label)
        self.tag_entry = gtk.Entry()
        hbox.pack_start(self.tag_entry)
        content_area.pack_end(hbox)
        hbox.show_all()
        self.connect('response', self.on_response)
        self.add_button('Close', gtk.RESPONSE_CLOSE)
        self.add_button('Add', gtk.RESPONSE_ACCEPT)
        self.set_default_response(gtk.RESPONSE_ACCEPT)

    def get_tag(self):
        return self._tag

    def on_response(self, dialog, response_id):
        self._tag = self.tag_entry.get_text().strip()
