# -*- coding utf-8 -*-

import gtk

from diglib.core.util import text_from_tags


class DocumentPropertiesDialog(gtk.Dialog):

    def __init__(self, parent, doc):
        super(DocumentPropertiesDialog, self).__init__(parent=parent)
        self.set_title('Document Properties')
        self.set_has_separator(False)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_border_width(4)
        self.set_default_size(500, 300)
        content_area = self.get_content_area()
        content_area.set_spacing(4)
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_shadow_type(gtk.SHADOW_OUT)
        model = gtk.ListStore(str, str)
        model.append(['<b>MD5</b>', doc.hash_md5])
        model.append(['<b>CTPH</b>', doc.hash_ssdeep])
        model.append(['<b>MIME Type</b>', doc.mime_type])
        model.append(['<b>Language Code</b>', doc.language_code])
        model.append(['<b>Tags</b>', text_from_tags(doc.tags)])
        model.append(['<b>Document Size</b>', doc.document_size])
        model.append(['<b>Document Path</b>', doc.document_abspath])
        model.append(['<b>Small Thumbnail Path</b>', doc.small_thumbnail_abspath])
        model.append(['<b>Normal Thumbnail Path</b>', doc.normal_thumbnail_abspath])
        model.append(['<b>Large Thumbnail Path</b>', doc.large_thumbnail_abspath])
        treeview = gtk.TreeView(model)
        name_renderer = gtk.CellRendererText()
        name_renderer.set_property('xalign', 1.0)
        name_renderer.set_property('background', self.get_style().bg[gtk.STATE_INSENSITIVE].to_string())
        value_renderer = gtk.CellRendererText()
        treeview.insert_column_with_attributes(0, 'Name', name_renderer, markup=0)
        treeview.insert_column_with_attributes(1, 'Value', value_renderer, text=1)
        treeview.set_headers_visible(False)
        scrolledwindow.add_with_viewport(treeview)
        content_area.pack_start(scrolledwindow)
        content_area.show_all()
        self.add_button('Close', gtk.RESPONSE_CLOSE)
        self.set_default_response(gtk.RESPONSE_CLOSE)
